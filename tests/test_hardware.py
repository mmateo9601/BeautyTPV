from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import Invoice, InvoiceLine
from apps.hardware.drivers import DeliveryUnknown, DriverUnavailable, send
from apps.hardware.escpos import CUT, DRAWER, render_receipt
from apps.hardware.models import Printer, PrintJob
from apps.hardware.services import (
    enqueue_invoice,
    enqueue_test,
    process_job,
    recover_expired,
    retry_job,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def actor():
    return User.objects.create_user(username="hardware", role="SUPERADMIN")


@pytest.fixture
def printer():
    return Printer.objects.create(name="Simulador QA", connection_type="SIMULATOR")


@pytest.fixture
def invoice(actor):
    obj = Invoice.objects.create(
        series="T",
        year=2026,
        number=1,
        issued_at=timezone.now(),
        issuer={"name": "Pruebas", "tax_id": "B12345678", "address": "Direccion"},
        total=Decimal("12.10"),
        net_total=Decimal("10.00"),
        tax_total=Decimal("2.10"),
        created_by=actor,
    )
    InvoiceLine.objects.create(
        invoice=obj,
        description="Manicura",
        quantity=1,
        unit_price=Decimal("12.10"),
        tax_rate=21,
        net_total=10,
        tax_total=Decimal("2.10"),
        total=Decimal("12.10"),
    )
    return obj


def test_receipt_snapshot_qr_cut(invoice):
    data = render_receipt(invoice)
    for value in [
        b"Manicura",
        invoice.full_number.encode(),
        b"SIN VALIDEZ FISCAL",
        b"ValidarQR",
        CUT,
    ]:
        assert value in data
    assert DRAWER not in data


def test_original_idempotent_copy_no_drawer(invoice, actor, printer):
    first = enqueue_invoice(invoice, actor)
    assert enqueue_invoice(invoice, actor).pk == first.pk
    copy = enqueue_invoice(invoice, actor, copy=True, open_drawer=True)
    assert copy.pk != first.pk and copy.kind == "COPY"
    assert b"COPIA" in bytes(copy.payload)
    assert not copy.open_drawer and DRAWER not in bytes(copy.payload)


def test_drawer_requires_cash(invoice, actor, printer):
    with pytest.raises(ValidationError):
        enqueue_invoice(invoice, actor, open_drawer=True)


def test_no_printer_pending(invoice, actor):
    job = enqueue_invoice(invoice, actor)
    assert not process_job(job.pk)
    job.refresh_from_db()
    assert job.status == "PENDING"


def test_simulator_done_once(actor, printer, settings):
    settings.DEBUG = True
    settings.HARDWARE_SIMULATOR = True
    job = enqueue_test(printer, actor)
    assert process_job(job.pk)
    job.refresh_from_db()
    assert job.status == "DONE" and job.attempts == 1
    assert not process_job(job.pk)


def test_production_refuses_simulator(printer, settings):
    settings.DEBUG = False
    settings.HARDWARE_SIMULATOR = True
    with pytest.raises(DriverUnavailable):
        send(printer, b"test")


def test_unknown_never_retried(actor, printer):
    job = enqueue_test(printer, actor, drawer=True)
    with patch("apps.hardware.services.send", side_effect=DeliveryUnknown):
        assert not process_job(job.pk)
    job.refresh_from_db()
    assert job.status == "UNKNOWN"
    with pytest.raises(ValidationError):
        retry_job(job, actor)
    assert not process_job(job.pk)


def test_prewrite_failure_retry(actor, printer):
    job = enqueue_test(printer, actor)
    with patch("apps.hardware.services.send", side_effect=DriverUnavailable):
        assert not process_job(job.pk)
    job.refresh_from_db()
    assert job.status == "FAILED"
    assert retry_job(job, actor).status == "PENDING"


def test_expired_lease_unknown(actor, printer):
    job = enqueue_test(printer, actor, drawer=True)
    PrintJob.objects.filter(pk=job.pk).update(
        status="SENDING", lease_until=timezone.now() - timedelta(minutes=5)
    )
    assert recover_expired() == 1
    job.refresh_from_db()
    assert job.status == "UNKNOWN"


def test_employee_cannot_test_drawer(actor, printer):
    actor.role = "EMPLOYEE"
    actor.save(update_fields=["role"])
    with pytest.raises(PermissionDenied):
        enqueue_test(printer, actor, drawer=True)


def test_text_cannot_inject_drawer(invoice):
    invoice.issuer["name"] = "hostile\x1bp\x00\x19\xfa"
    assert DRAWER not in render_receipt(invoice)


def test_job_intent_immutable(invoice, actor, printer):
    job = enqueue_invoice(invoice, actor)
    job.open_drawer = True
    with pytest.raises(ValidationError):
        job.save()


def test_tcp_prewrite_failure(printer):
    printer.connection_type = "TCP"
    with patch("apps.hardware.drivers.socket.create_connection", side_effect=OSError):
        with pytest.raises(DriverUnavailable):
            send(printer, b"test")


def test_tcp_midwrite_unknown(printer):
    printer.connection_type = "TCP"
    with patch("apps.hardware.drivers.socket.create_connection") as connect:
        connect.return_value.sendall.side_effect = OSError
        with pytest.raises(DeliveryUnknown):
            send(printer, b"test")
