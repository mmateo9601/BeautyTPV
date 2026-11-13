from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.billing.services import production_guard
from apps.core.models import CompanySettings

from .models import FiscalEndpointState, FiscalOutbox, FiscalRecord, FiscalTransmission
from .protocol import (
    ENDPOINTS,
    build_xml,
    canonical_hash,
    fiscal_date,
    parse_response,
    response_wait_seconds,
    soap_envelope,
    validate_response,
    validate_xml,
    verify_record_snapshot,
)


@transaction.atomic
def create_record(
    invoice, record_type="ALTA", correction=False, without_previous=False, rejected_previous=True
):
    from apps.core.guards import require_operational

    require_operational()
    company = CompanySettings.load()
    previous = FiscalRecord.objects.select_related("invoice").order_by("-pk").first()
    generated_at = (
        timezone.now().astimezone(ZoneInfo(company.timezone)).isoformat(timespec="seconds")
    )
    suffix = "Anulada" if record_type == "ANULACION" else ""
    values = {
        "IDEmisorFactura" + suffix: invoice.issuer.get("tax_id", ""),
        "NumSerieFactura" + suffix: invoice.full_number,
        "FechaExpedicionFactura" + suffix: fiscal_date(invoice),
        "TipoFactura": invoice.invoice_type,
        "CuotaTotal": format(invoice.tax_total, ".2f"),
        "ImporteTotal": format(invoice.total, ".2f"),
        "Huella": previous.fingerprint if previous else "",
        "FechaHoraHusoGenRegistro": generated_at,
    }
    canonical, fingerprint = canonical_hash(values, record_type)
    xml = build_xml(
        invoice,
        previous,
        generated_at,
        fingerprint,
        record_type,
        correction,
        without_previous,
        rejected_previous,
    )
    if invoice.fiscal_mode == "PRODUCTION":
        production_guard(company, mode=invoice.fiscal_mode)
        validate_xml(xml)
    item = FiscalRecord.objects.create(
        invoice=invoice,
        record_type=record_type,
        previous=previous,
        fingerprint=fingerprint,
        canonical_payload=canonical,
        generated_at=generated_at,
        xml=xml,
    )
    FiscalOutbox.objects.create(record=item)
    return item


def verify_chain():
    previous = None
    for item in (
        FiscalRecord.objects.select_related("invoice")
        .prefetch_related("invoice__lines")
        .order_by("pk")
    ):
        if item.previous_id != (previous.pk if previous else None):
            return False
        try:
            valid = verify_record_snapshot(item, previous)
        except (ValueError, ArithmeticError, KeyError, SyntaxError):
            return False
        if not valid:
            return False
        previous = item
    return True


@transaction.atomic
def correct_rejected(record, actor):
    from apps.accounts.permissions import require_role
    from apps.audit.services import record as audit

    require_role(actor, "ADMIN")
    prior_status = (
        FiscalOutbox.objects.filter(record=record).values_list("status", flat=True).first()
    )
    if prior_status not in ("REJECTED", "ACCEPTED_WITH_ERRORS"):
        raise ValidationError(
            "Solo puede subsanarse un registro rechazado o aceptado con errores, conservando el original."
        )
    if record.invoice.fiscal_records.filter(
        pk__gt=record.pk, record_type=record.record_type
    ).exists():
        raise ValidationError(
            "Ya existe un registro posterior; revise su resultado antes de subsanar."
        )
    from lxml import etree

    from .protocol import SF

    original_xml = etree.fromstring(
        record.xml.encode(), etree.XMLParser(resolve_entities=False, no_network=True)
    )
    without_previous = original_xml.xpath(
        "boolean(//sf:RegistroAnulacion/sf:SinRegistroPrevio[text()='S'])", namespaces={"sf": SF}
    )
    corrected = create_record(
        record.invoice,
        record_type=record.record_type,
        correction=True,
        without_previous=without_previous,
        rejected_previous=prior_status == "REJECTED",
    )
    audit(actor, "fiscal.correction", str(record.pk))
    return corrected


@transaction.atomic
def annul_record(record, actor, reason, *, without_previous=False):
    from apps.accounts.permissions import require_role
    from apps.audit.services import record as audit

    require_role(actor, "ADMIN")
    if not reason.strip():
        raise ValidationError(
            "Motivo obligatorio. Para devoluciones utilice factura rectificativa."
        )
    if record.invoice.fiscal_records.filter(record_type="ANULACION").exists():
        raise ValidationError("Registro ya anulado.")
    item = create_record(record.invoice, "ANULACION", without_previous=without_previous)
    audit(actor, "fiscal.annul", str(record.pk), metadata={"reason": reason})
    return item


def send_one(pk=None, transport=None):
    """Lease/CAS short transactions; network outside atomic; never synthesize AEAT acceptance."""
    restore_marker = Path(str(settings.DATABASES["default"]["NAME"]) + ".fiscal-restore-hold")
    if getattr(settings, "FISCAL_RESTORE_HOLD", False) or restore_marker.exists():
        raise ValidationError("Remisión retenida tras restauración: reconciliar antes de reanudar.")
    now = timezone.now()
    token = uuid4().hex
    with transaction.atomic():
        eligible = FiscalOutbox.objects.filter(
            Q(status__in=["PENDING", "RETRY"], next_attempt_at__lte=now)
            | Q(status="SENDING", lease_until__lt=now)
        )
        if pk is not None:
            eligible = eligible.filter(pk=pk)
        item = eligible.select_related("record__invoice").order_by("pk").first()
        if not item:
            return None
        state, _ = FiscalEndpointState.objects.get_or_create(
            environment=item.record.invoice.fiscal_mode,
            defaults={"next_allowed_at": now},
        )
        available = FiscalEndpointState.objects.filter(
            pk=state.pk, next_allowed_at__lte=now
        ).filter(Q(lease_until__isnull=True) | Q(lease_until__lt=now))
        if not available.update(lease_until=now + timedelta(minutes=2), lease_token=token):
            return None
        if not eligible.filter(pk=item.pk).update(
            status="SENDING",
            lease_until=now + timedelta(minutes=2),
            lease_token=token,
            attempts=F("attempts") + 1,
        ):
            FiscalEndpointState.objects.filter(pk=state.pk, lease_token=token).update(
                lease_until=None, lease_token=""
            )
            return None
        item.refresh_from_db()
    response_text = ""
    wait_seconds = 60
    try:
        invoice = item.record.invoice
        if invoice.fiscal_mode == "PRODUCTION":
            production_guard(CompanySettings.load(), mode=invoice.fiscal_mode)
        validate_xml(item.record.xml)
        from apps.support.fiscal import fiscal_configuration

        configuration = fiscal_configuration()
        if configuration["environment"] != invoice.fiscal_mode:
            raise ValidationError(
                "El entorno configurado no coincide con el registro inmutable pendiente."
            )
        certificate = configuration["certificate"]
        private_key = configuration["private_key"]
        if transport is None and (not certificate or not private_key):
            raise ValidationError(
                "Certificado cliente AEAT no configurado; registro pendiente de remisión."
            )
        if transport is not None and not getattr(settings, "TESTING", False):
            raise ValidationError("Transporte simulado permitido solo en tests.")
        sender = transport or requests.post
        response = sender(
            ENDPOINTS[invoice.fiscal_mode],
            data=soap_envelope(item.record.xml),
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'},
            cert=(certificate, private_key),
            timeout=(10, 45),
        )
        response.raise_for_status()
        response_text = response.content.decode("utf-8")[:1000000]
        validate_response(response.content, invoice, record_type=item.record.record_type)
        status, error = parse_response(response.content)
        wait_seconds = response_wait_seconds(response.content)
    except Exception as exc:
        status = "RETRY"
        # Avoid exception strings containing certificate paths, HTTP credentials or PII.
        error = f"{type(exc).__name__}: remisión no confirmada; revisar configuración y conexión."
    with transaction.atomic():
        FiscalTransmission.objects.create(outbox=item, response=response_text, status=status)
        committed = FiscalOutbox.objects.filter(
            pk=item.pk, status="SENDING", lease_token=token
        ).update(
            status=status,
            lease_until=None,
            lease_token="",
            last_error=error,
            next_attempt_at=timezone.now()
            + timedelta(seconds=min(3600, 60 * 2 ** min(item.attempts, 6))),
        )
        FiscalEndpointState.objects.filter(pk=state.pk, lease_token=token).update(
            lease_until=None,
            lease_token="",
            next_allowed_at=timezone.now() + timedelta(seconds=wait_seconds),
        )
    return status if committed else "LEASE_LOST"
