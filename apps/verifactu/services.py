from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.billing.services import production_guard
from apps.core.models import CompanySettings

from .models import FiscalOutbox, FiscalRecord, FiscalTransmission
from .protocol import (
    ENDPOINTS,
    build_xml,
    canonical_hash,
    fiscal_date,
    parse_response,
    soap_envelope,
    validate_response,
    validate_xml,
)


@transaction.atomic
def create_record(invoice, record_type="ALTA", correction=False):
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
    xml = build_xml(invoice, previous, generated_at, fingerprint, record_type, correction)
    if invoice.fiscal_mode == "PRODUCTION":
        production_guard(company)
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
    import hashlib

    previous = None
    for item in FiscalRecord.objects.order_by("pk"):
        if item.previous_id != (previous.pk if previous else None):
            return False
        if (
            hashlib.sha256(item.canonical_payload.encode("utf-8")).hexdigest().upper()
            != item.fingerprint
        ):
            return False
        expected_previous = previous.fingerprint if previous else ""
        if f"&Huella={expected_previous}&FechaHoraHusoGenRegistro=" not in item.canonical_payload:
            return False
        previous = item
    return True


@transaction.atomic
def correct_rejected(record, actor):
    from apps.accounts.permissions import require_role
    from apps.audit.services import record as audit

    require_role(actor, "ADMIN")
    if record.outbox.status != "REJECTED":
        raise ValidationError(
            "Solo puede subsanarse un registro rechazado, conservando el original."
        )
    if record.invoice.fiscal_records.filter(pk__gt=record.pk, record_type="ALTA").exists():
        raise ValidationError(
            "Ya existe un registro posterior; revise su resultado antes de subsanar."
        )
    corrected = create_record(record.invoice, correction=True)
    audit(actor, "fiscal.correction", str(record.pk))
    return corrected


@transaction.atomic
def annul_record(record, actor, reason):
    from apps.accounts.permissions import require_role
    from apps.audit.services import record as audit

    require_role(actor, "ADMIN")
    if not reason.strip():
        raise ValidationError(
            "Motivo obligatorio. Para devoluciones utilice factura rectificativa."
        )
    if record.invoice.fiscal_records.filter(record_type="ANULACION").exists():
        raise ValidationError("Registro ya anulado.")
    item = create_record(record.invoice, "ANULACION")
    audit(actor, "fiscal.annul", str(record.pk))
    return item


def send_one(pk=None, transport=None):
    """Lease/CAS short transactions; network outside atomic; never synthesize AEAT acceptance."""
    restore_marker = Path(str(settings.DATABASES["default"]["NAME"]) + ".fiscal-restore-hold")
    if getattr(settings, "FISCAL_RESTORE_HOLD", False) or restore_marker.exists():
        raise ValidationError("Remisión retenida tras restauración: reconciliar antes de reanudar.")
    now = timezone.now()
    eligible = FiscalOutbox.objects.filter(
        Q(status__in=["PENDING", "RETRY"], next_attempt_at__lte=now)
        | Q(status="SENDING", lease_until__lt=now)
    )
    if pk is not None:
        eligible = eligible.filter(pk=pk)
    item = eligible.order_by("pk").first()
    if not item:
        return None
    if not eligible.filter(pk=item.pk).update(
        status="SENDING", lease_until=now + timedelta(minutes=2), attempts=F("attempts") + 1
    ):
        return None
    item.refresh_from_db()
    response_text = ""
    try:
        invoice = item.record.invoice
        if invoice.fiscal_mode == "PRODUCTION":
            production_guard(CompanySettings.load())
        validate_xml(item.record.xml)
        certificate = getattr(settings, "AEAT_CERTIFICATE", "")
        private_key = getattr(settings, "AEAT_PRIVATE_KEY", "")
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
        validate_response(response.content, invoice)
        status, error = parse_response(response.content)
    except Exception as exc:
        status = "RETRY"
        # Avoid exception strings containing certificate paths, HTTP credentials or PII.
        error = f"{type(exc).__name__}: remisión no confirmada; revisar configuración y conexión."
    with transaction.atomic():
        FiscalTransmission.objects.create(outbox=item, response=response_text, status=status)
        FiscalOutbox.objects.filter(pk=item.pk).update(
            status=status,
            lease_until=None,
            last_error=error,
            next_attempt_at=timezone.now()
            + timedelta(seconds=min(3600, 60 * 2 ** min(item.attempts, 6))),
        )
    return status
