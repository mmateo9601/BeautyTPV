"""Acceptance services use real ORM/transactions; external devices are explicit simulators."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, connection, transaction
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import create_user
from apps.billing.models import Invoice
from apps.billing.services import rectify_invoice, render_pdf
from apps.cash.models import CashRegister, CashSession
from apps.cash.services import close_session, open_session
from apps.catalog.models import CatalogItem
from apps.core.models import CompanySettings
from apps.hardware.drivers import DriverUnavailable
from apps.hardware.escpos import DRAWER
from apps.hardware.models import Printer, PrintJob
from apps.hardware.services import enqueue_invoice, process_job
from apps.layout.models import Section, Station
from apps.pos.models import Payment, Sale
from apps.pos.services import add_line, checkout, open_ticket
from apps.verifactu.models import FiscalRecord
from apps.verifactu.protocol import validate_xml
from apps.verifactu.services import correct_rejected, send_one, verify_chain

pytestmark = pytest.mark.django_db


@pytest.fixture
def centre(settings):
    settings.DEBUG = True
    settings.HARDWARE_SIMULATOR = True
    settings.TESTING = True
    settings.FISCAL_PRODUCER = {"name": "Productor QA", "tax_id": "89890001K"}
    employee = User.objects.create_user(username="qa-employee", role="EMPLOYEE")
    manager = User.objects.create_user(username="qa-manager", role="MANAGER")
    admin = User.objects.create_user(username="qa-admin", role="ADMIN")
    company = CompanySettings.load()
    company.name = "Centro QA"
    company.tax_id = "89890001K"
    company.address = "Calle de pruebas 1"
    company.save()
    section = Section.objects.create(name="QA")
    station = Station.objects.create(section=section, name="Manicura", code="QA1")
    item = CatalogItem.objects.create(name="Manicura QA", price="24.20", tax_rate="21")
    register = CashRegister.objects.create(name="Caja QA")
    session = open_session(register, employee, "50.00")
    printer = Printer.objects.create(name="Simulador QA", connection_type="SIMULATOR")
    ticket = open_ticket(station, employee)
    return SimpleNamespace(**locals())


def sell(centre, method="CASH", key="qa-sale"):
    add_line(centre.ticket, centre.item, centre.employee)
    payment = {"method": method, "amount": "24.20"}
    if method == "CASH":
        payment["received"] = "30.00"
    else:
        payment["reference"] = "CONFIRMED-EXTERNAL-TERMINAL"
    return checkout(centre.ticket, centre.employee, [payment], key, centre.session)


def test_e01_cash_sale_invoice_spool_and_closure(centre):
    sale = sell(centre)
    assert sale.total == Decimal("24.20")
    assert sale.invoice.total == sale.total
    assert centre.session.expected_balance == Decimal("74.20")
    assert sale.payments.get().change == Decimal("5.80")
    centre.ticket.refresh_from_db()
    assert centre.ticket.status == "CLOSED"
    assert open_ticket(centre.station, centre.employee).pk != centre.ticket.pk
    job = sale.invoice.print_jobs.get(kind="RECEIPT")
    assert job.open_drawer and DRAWER in bytes(job.payload)
    assert process_job(job.pk)  # Simulated IO, never a physical-hardware claim.
    job.refresh_from_db()
    assert job.status == "DONE"
    assert validate_xml(sale.invoice.fiscal_records.get().xml)
    assert render_pdf(sale.invoice).startswith(b"%PDF")
    close_session(centre.session, centre.manager, "74.20")
    centre.session.refresh_from_db()
    assert centre.session.difference == 0


def test_e03_multiple_tax_rates_and_authorized_discount(centre):
    add_line(centre.ticket, centre.item, centre.employee)
    product = CatalogItem.objects.create(
        name="Producto QA", kind="PRODUCT", price="11.00", tax_rate="10"
    )
    with pytest.raises(PermissionDenied):
        add_line(centre.ticket, product, centre.employee, discount_percent="10")
    add_line(centre.ticket, product, centre.manager, discount_percent="10")
    sale = checkout(
        centre.ticket,
        centre.manager,
        [{"method": "CARD", "amount": "34.10", "reference": "CONFIRMED"}],
        "qa-tax",
    )
    amounts = {
        line.tax_rate: (line.net_total, line.tax_total, line.total)
        for line in sale.invoice.lines.all()
    }
    assert amounts[Decimal("21")] == (Decimal("20"), Decimal("4.20"), Decimal("24.20"))
    assert amounts[Decimal("10")] == (Decimal("9"), Decimal("0.90"), Decimal("9.90"))
    assert sale.invoice.net_total + sale.invoice.tax_total == sale.total


def test_e04_mixed_cash_only_component_in_cash_balance(centre):
    add_line(centre.ticket, centre.item, centre.employee)
    payments = [
        {"method": "CASH", "amount": "10.00", "received": "20.00"},
        {"method": "CARD", "amount": "14.20", "reference": "CONFIRMED"},
    ]
    sale = checkout(centre.ticket, centre.employee, payments, "qa-mixed", centre.session)
    assert sum(sale.payments.values_list("amount", flat=True)) == sale.total
    assert centre.session.expected_balance == Decimal("60.00")
    assert sale.payments.get(method="CASH").change == Decimal("10.00")
    assert checkout(centre.ticket, centre.employee, payments, "qa-mixed", centre.session) == sale
    assert Sale.objects.count() == Invoice.objects.count() == FiscalRecord.objects.count() == 1


def test_e06_printer_failure_keeps_sale_and_controlled_copy(centre):
    sale = sell(centre)
    invoice = sale.invoice
    original = invoice.print_jobs.get()
    with patch("apps.hardware.services.send", side_effect=DriverUnavailable):
        assert not process_job(original.pk)
    original.refresh_from_db()
    assert original.status == "FAILED"
    assert sale.pk == Sale.objects.get().pk and Invoice.objects.get().pk == invoice.pk
    copy = enqueue_invoice(invoice, centre.employee, copy=True, open_drawer=True)
    assert copy.kind == "COPY" and not copy.open_drawer
    assert b"COPIA" in bytes(copy.payload) and DRAWER not in bytes(copy.payload)
    assert Invoice.objects.count() == FiscalRecord.objects.count() == 1


def test_e07_network_loss_does_not_regenerate_fiscal_record(centre):
    import requests

    invoice = sell(centre).invoice
    record = invoice.fiscal_records.get()
    original = (record.pk, record.xml, record.fingerprint)

    def offline_transport(*args, **kwargs):
        raise requests.ConnectionError("Explicit QA network-outage fixture")

    assert send_one(record.outbox.pk, transport=offline_transport) == "RETRY"
    record.refresh_from_db()
    assert (record.pk, record.xml, record.fingerprint) == original
    record.outbox.refresh_from_db()
    assert record.outbox.status == "RETRY"
    assert record.outbox.transmissions.get().status == "RETRY"
    assert verify_chain() and FiscalRecord.objects.count() == 1


def test_e08_rejected_correction_preserves_original(centre):
    from lxml import etree

    from apps.verifactu.protocol import SF, SOAP, child, fiscal_date

    record = sell(centre).invoice.fiscal_records.get()
    original = (record.xml, record.fingerprint)
    # Synthetic official-schema rejection fixture; not an AEAT integration receipt.
    namespace = SF.replace("SuministroInformacion", "RespuestaSuministro")
    envelope = etree.Element(f"{{{SOAP}}}Envelope")
    body = child(envelope, "Body", namespace=SOAP)
    response = child(body, "RespuestaRegFactuSistemaFacturacion", namespace=namespace)
    header = child(response, "Cabecera", namespace=namespace)
    issuer = child(header, "ObligadoEmision")
    child(issuer, "NombreRazon", record.invoice.issuer["name"])
    child(issuer, "NIF", record.invoice.issuer["tax_id"])
    child(response, "TiempoEsperaEnvio", "60", namespace=namespace)
    child(response, "EstadoEnvio", "Incorrecto", namespace=namespace)
    line = child(response, "RespuestaLinea", namespace=namespace)
    identity = child(line, "IDFactura", namespace=namespace)
    child(identity, "IDEmisorFactura", record.invoice.issuer["tax_id"])
    child(identity, "NumSerieFactura", record.invoice.full_number)
    child(identity, "FechaExpedicionFactura", fiscal_date(record.invoice))
    child(child(line, "Operacion", namespace=namespace), "TipoOperacion", "Alta")
    child(line, "EstadoRegistro", "Incorrecto", namespace=namespace)
    child(line, "CodigoErrorRegistro", "1100", namespace=namespace)
    content = etree.tostring(envelope)
    transport_response = SimpleNamespace(content=content, raise_for_status=lambda: None)
    assert (
        send_one(record.outbox.pk, transport=lambda *args, **kwargs: transport_response)
        == "REJECTED"
    )
    record.outbox.refresh_from_db()
    assert record.outbox.transmissions.get().response == content.decode()
    assert record.outbox.last_error == "1100"
    correction = correct_rejected(record, centre.admin)
    record.refresh_from_db()
    assert (record.xml, record.fingerprint) == original
    assert correction.pk != record.pk and correction.previous_id == record.pk
    assert correction.invoice_id == record.invoice_id
    assert "Subsanacion" in correction.xml and validate_xml(correction.xml)
    assert record.outbox.status == "REJECTED" and correction.outbox.status == "PENDING"
    assert verify_chain()


def test_e09_e16_sql_immutability_and_historical_price_snapshot(centre):
    invoice = sell(centre).invoice
    original_line = invoice.lines.get()
    centre.item.price = Decimal("99.99")
    centre.item.name = "Precio cambiado"
    centre.item.save()
    original_line.refresh_from_db()
    assert original_line.description == "Manicura QA" and original_line.unit_price == Decimal(
        "24.20"
    )
    assert invoice.total == Decimal("24.20")
    with pytest.raises(ValidationError):
        invoice.delete()
    with pytest.raises(ValidationError):
        Invoice.objects.filter(pk=invoice.pk).update(total=0)
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("UPDATE billing_invoice SET total=0 WHERE id=%s", [invoice.pk])
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("DELETE FROM billing_invoice WHERE id=%s", [invoice.pk])
    invoice.refresh_from_db()
    assert invoice.total == Decimal("24.20")


def test_e10_e11_roles_reject_backend_privilege_escalation(centre):
    client = Client()
    client.force_login(centre.employee)
    assert client.get("/informes/").status_code == 403
    assert client.get("/auditoria/").status_code == 403
    assert (
        client.post(f"/caja/{centre.session.pk}/cerrar/", {"counted": "50.00"}).status_code == 403
    )
    with pytest.raises(PermissionDenied):
        close_session(centre.session, centre.employee, "50.00")
    with pytest.raises(PermissionDenied):
        create_user(
            centre.admin, username="escalation", role="SUPERADMIN", password="Safe-Password-118!"
        )
    assert not User.objects.filter(username="escalation").exists()


def test_e14_card_receipt_never_opens_drawer_software_only(centre):
    sale = sell(centre, method="CARD")
    job = PrintJob.objects.get(invoice=sale.invoice)
    assert not job.open_drawer and DRAWER not in bytes(job.payload)
    assert b"ValidarQR" in bytes(job.payload)
    assert Payment.objects.get(sale=sale).method == "CARD"


def test_e11_superadmin_diagnostic_requires_elevation_and_authorization(centre):
    from apps.audit.models import AuditEvent
    from apps.support.services import authorize_support

    superadmin = User.objects.create_user(username="qa-superadmin", role="SUPERADMIN")
    centre.admin.set_password("Safe-Approval-Password-172!")
    centre.admin.save()
    client = Client()
    client.force_login(centre.employee)
    assert client.get("/soporte/").status_code == 403
    client.force_login(superadmin)
    assert client.post("/soporte/diagnostico/").status_code == 403
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 300
    session.save()
    assert client.post("/soporte/diagnostico/").status_code == 403
    authorization = authorize_support(
        superadmin,
        centre.admin.username,
        "Safe-Approval-Password-172!",
        "Verificar diagnóstico autorizado de aceptación",
    )
    response = client.post("/soporte/diagnostico/")
    assert response.status_code == 200 and response.json()["integrity"] == "ok"
    assert AuditEvent.objects.filter(actor=superadmin, action="support.diagnostic").exists()
    authorization.revoked_at = timezone.now()
    authorization.save()
    assert client.post("/soporte/diagnostico/").status_code == 403


def test_e15_rectification_reconciles_cash_and_report(centre):
    sale = sell(centre)
    invoice = sale.invoice
    rectification = rectify_invoice(
        invoice, centre.manager, "Devolución QA", method="CASH", cash_session=centre.session
    )
    assert rectification.rectifies_id == invoice.pk
    assert rectification.total == -invoice.total
    assert centre.session.expected_balance == Decimal("50.00")
    assert verify_chain()
    assert validate_xml(rectification.fiscal_records.get().xml)
    client = Client()
    client.force_login(centre.manager)
    response = client.get("/informes/")
    assert response.status_code == 200
    assert response.context["totals"]["net"] == Decimal("0")
    assert sum(row["total"] for row in response.context["payments"]) == Decimal("0")
    assert sum(response.context["employees"].values()) == Decimal("0")
    assert sum(response.context["items"].values()) == Decimal("0")
    assert sum(row["tax_total"] for row in response.context["tax_totals"]) == Decimal("0")
    with pytest.raises(ValidationError):
        rectify_invoice(invoice, centre.manager, "Duplicada", reference="EXTERNAL-REFUND")


def test_e15_refund_rechecks_closed_cash_session_from_database(centre):
    invoice = sell(centre).invoice
    stale_session = CashSession.objects.get(pk=centre.session.pk)
    close_session(centre.session, centre.manager, "74.20")
    assert stale_session.closed_at is None
    with pytest.raises(ValidationError):
        rectify_invoice(
            invoice,
            centre.manager,
            "No devolver desde caja cerrada",
            method="CASH",
            cash_session=stale_session,
        )
    assert not invoice.rectifications.exists()
    assert Invoice.objects.count() == 1
