from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.verifactu.protocol import canonical_hash, parse_response, qr_url, validate_xml


def test_official_aeat_hash_vectors():
    """AEAT huella v0.1.2, 27/08/2024, sections 6.1-6.3, pages 10-12."""
    values = dict(
        IDEmisorFactura="89890001K",
        NumSerieFactura="12345678/G33",
        FechaExpedicionFactura="01-01-2024",
        TipoFactura="F1",
        CuotaTotal="12.35",
        ImporteTotal="123.45",
        Huella="",
        FechaHoraHusoGenRegistro="2024-01-01T19:20:30+01:00",
    )
    _, first = canonical_hash(values)
    assert first == "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60"
    values.update(
        NumSerieFactura="12345679/G34",
        Huella=first,
        FechaHoraHusoGenRegistro="2024-01-01T19:20:35+01:00",
    )
    _, second = canonical_hash(values)
    assert second == "F7B94CFD8924EDFF273501B01EE5153E4CE8F259766F88CF6ACB8935802A2B97"
    _, third = canonical_hash(
        dict(
            IDEmisorFacturaAnulada="89890001K",
            NumSerieFacturaAnulada="12345679/G34",
            FechaExpedicionFacturaAnulada="01-01-2024",
            Huella=second,
            FechaHoraHusoGenRegistro="2024-01-01T19:20:40+01:00",
        ),
        "ANULACION",
    )
    assert third == "177547C0D57AC74748561D054A9CEC14B4C4EA23D1BEFD6F2E69E3A388F90C68"


def test_qr_official_url_encoding():
    from datetime import datetime

    invoice = SimpleNamespace(
        fiscal_mode="TEST",
        issuer={"tax_id": "89890001K"},
        full_number="12345678&G33",
        issued_at=datetime(2024, 1, 1),
        total=Decimal("241.40"),
    )
    assert (
        qr_url(invoice)
        == "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR?nif=89890001K&numserie=12345678%26G33&fecha=01-01-2024&importe=241.40"
    )


def test_response_never_assumes_acceptance():
    assert parse_response(
        b"<root><EstadoRegistro>Incorrecto</EstadoRegistro><CodigoErrorRegistro>1100</CodigoErrorRegistro></root>"
    ) == ("REJECTED", "1100")
    assert (
        parse_response(b"<root><EstadoRegistro>AceptadoConErrores</EstadoRegistro></root>")[0]
        == "ACCEPTED_WITH_ERRORS"
    )
    with pytest.raises(ValueError):
        parse_response(b"<html>Error</html>")


def response_fixture(invoice, state="Correcto", code=""):
    """Synthetic official-schema fixture; never an AEAT execution receipt."""
    from lxml import etree

    from apps.verifactu.protocol import SF, SOAP, child, fiscal_date

    response_ns = SF.replace("SuministroInformacion", "RespuestaSuministro")
    envelope = etree.Element(f"{{{SOAP}}}Envelope")
    body = child(envelope, "Body", namespace=SOAP)
    response = child(body, "RespuestaRegFactuSistemaFacturacion", namespace=response_ns)
    header = child(response, "Cabecera", namespace=response_ns)
    issuer = child(header, "ObligadoEmision")
    child(issuer, "NombreRazon", invoice.issuer["name"])
    child(issuer, "NIF", invoice.issuer["tax_id"])
    child(response, "TiempoEsperaEnvio", "60", namespace=response_ns)
    child(
        response,
        "EstadoEnvio",
        "Incorrecto" if state == "Incorrecto" else "Correcto",
        namespace=response_ns,
    )
    line = child(response, "RespuestaLinea", namespace=response_ns)
    identity = child(line, "IDFactura", namespace=response_ns)
    child(identity, "IDEmisorFactura", invoice.issuer["tax_id"])
    child(identity, "NumSerieFactura", invoice.full_number)
    child(identity, "FechaExpedicionFactura", fiscal_date(invoice))
    operation = child(line, "Operacion", namespace=response_ns)
    child(operation, "TipoOperacion", "Alta")
    child(line, "EstadoRegistro", state, namespace=response_ns)
    if code:
        child(line, "CodigoErrorRegistro", code, namespace=response_ns)
    return etree.tostring(envelope)


@pytest.mark.django_db
def test_soap_schema_identity_and_receipt_persistence(fiscal_sale):
    from apps.billing.services import issue_invoice
    from apps.verifactu.protocol import validate_response
    from apps.verifactu.services import send_one

    sale, actor = fiscal_sale
    with override_settings(FISCAL_PRODUCER={"name": "Productor prueba", "tax_id": "89890001K"}):
        invoice = issue_invoice(sale, actor)
    content = response_fixture(invoice)
    assert validate_response(content, invoice)
    response = SimpleNamespace(content=content, raise_for_status=lambda: None)
    with override_settings(TESTING=True):
        assert (
            send_one(
                invoice.fiscal_records.get().outbox.pk, transport=lambda *args, **kwargs: response
            )
            == "ACCEPTED"
        )
    item = invoice.fiscal_records.get().outbox
    assert item.transmissions.get().response == content.decode()
    wrong = content.replace(invoice.full_number.encode(), b"UNKNOWN-NUMBER")
    with pytest.raises(ValueError):
        validate_response(wrong, invoice)


@pytest.mark.django_db
def test_rejected_correction_flags_and_anulacion_xsd(fiscal_sale):
    from apps.billing.services import issue_invoice
    from apps.verifactu.models import FiscalOutbox
    from apps.verifactu.services import annul_record, correct_rejected

    sale, actor = fiscal_sale
    actor.role = "ADMIN"
    actor.save()
    with override_settings(FISCAL_PRODUCER={"name": "Productor prueba", "tax_id": "89890001K"}):
        invoice = issue_invoice(sale, actor)
        original = invoice.fiscal_records.get()
        FiscalOutbox.objects.filter(record=original).update(status="REJECTED")
        corrected = correct_rejected(original, actor)
        annulment = annul_record(corrected, actor, "Registro emitido por error; no devolución")
    assert "<sf:Subsanacion>S</sf:Subsanacion>" in corrected.xml
    assert "<sf:RechazoPrevio>X</sf:RechazoPrevio>" in corrected.xml
    assert validate_xml(corrected.xml)
    assert validate_xml(annulment.xml)


@pytest.fixture
def fiscal_sale(db):
    from apps.accounts.models import User
    from apps.core.models import CompanySettings
    from apps.pos.models import OpenTicket, Sale, TicketLine

    company = CompanySettings.load()
    company.name = "Empresa prueba"
    company.tax_id = "89890001K"
    company.address = "Prueba 1"
    company.save()
    actor = User.objects.create_user(
        username="fiscal", password="Testing-Password-172!", role="MANAGER"
    )
    ticket = OpenTicket.objects.create(created_by=actor)
    TicketLine.objects.create(
        ticket=ticket,
        description="Servicio",
        quantity=1,
        unit_price=Decimal("121"),
        tax_rate=Decimal("21"),
    )
    sale = Sale.objects.create(
        ticket=ticket,
        total=Decimal("121"),
        created_by=actor,
        idempotency_key="fiscal-sale",
        request_fingerprint="a" * 64,
    )
    return sale, actor


@pytest.mark.django_db
def test_invoice_chain_immutable_and_official_xsd(fiscal_sale):
    from apps.billing.services import issue_invoice
    from apps.verifactu.services import verify_chain

    sale, actor = fiscal_sale
    with override_settings(
        FISCAL_PRODUCER={
            "name": "Productor prueba",
            "tax_id": "89890001K",
            "installation_id": "TEST-1",
        }
    ):
        invoice = issue_invoice(sale, actor)
    item = invoice.fiscal_records.get()
    assert validate_xml(item.xml)
    assert verify_chain()
    assert issue_invoice(sale, actor).pk == invoice.pk
    invoice.total = Decimal("1")
    with pytest.raises(ValidationError):
        invoice.save()
    with pytest.raises(ValidationError):
        invoice.delete()
    assert invoice.lines.get().net_total == Decimal("100")


@pytest.mark.django_db
def test_production_fail_closed(fiscal_sale):
    from apps.billing.services import issue_invoice
    from apps.core.models import CompanySettings

    sale, actor = fiscal_sale
    company = CompanySettings.load()
    company.fiscal_mode = "PRODUCTION"
    company.save()
    with override_settings(FISCAL_PRODUCTION_APPROVED=False):
        with pytest.raises(ValidationError):
            issue_invoice(sale, actor)


@pytest.mark.django_db
def test_refund_preserves_original_and_schema(fiscal_sale):
    from apps.billing.services import issue_invoice, rectify_invoice
    from apps.verifactu.services import verify_chain

    sale, actor = fiscal_sale
    with override_settings(FISCAL_PRODUCER={"name": "Productor prueba", "tax_id": "89890001K"}):
        original = issue_invoice(sale, actor)
        refund = rectify_invoice(original, actor, "Devolución total", reference="refund-confirmed")
    assert refund.total == -original.total
    assert refund.invoice_type == "R5"
    assert validate_xml(refund.fiscal_records.get().xml)
    assert verify_chain()
    with pytest.raises(ValidationError):
        rectify_invoice(original, actor, "Otra", reference="x")


@pytest.mark.django_db
def test_network_failure_persists_chain(fiscal_sale):
    from apps.billing.services import issue_invoice
    from apps.verifactu.services import send_one, verify_chain

    sale, actor = fiscal_sale
    with override_settings(FISCAL_PRODUCER={"name": "Productor prueba", "tax_id": "89890001K"}):
        invoice = issue_invoice(sale, actor)
    item = invoice.fiscal_records.get().outbox
    assert send_one(item.pk) == "RETRY"
    item.refresh_from_db()
    assert item.status == "RETRY" and item.attempts == 1
    assert verify_chain()


@pytest.mark.django_db
def test_restore_hold_marker_blocks_remission(fiscal_sale, tmp_path):
    from pathlib import Path

    from django.conf import settings

    from apps.verifactu.services import send_one

    marker = Path(str(settings.DATABASES["default"]["NAME"]) + ".fiscal-restore-hold")
    marker.write_text("Test hold", encoding="utf-8")
    try:
        with pytest.raises(ValidationError):
            send_one()
    finally:
        marker.unlink()


@pytest.mark.django_db
def test_pdf_contains_snapshot_and_test_label(fiscal_sale):
    import io

    from pypdf import PdfReader

    from apps.billing.services import issue_invoice, render_pdf

    sale, actor = fiscal_sale
    invoice = issue_invoice(sale, actor)
    content = render_pdf(invoice)
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(content)).pages)
    assert invoice.full_number in text
    assert "SIN VALIDEZ FISCAL PRODUCTIVA" in text
    assert "121.00" in text
