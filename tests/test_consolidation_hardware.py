"""Configured output and protected device maintenance; no physical IO."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from test_acceptance import centre as centre
from test_acceptance import sell
from test_hardware import actor as actor
from test_hardware import invoice as invoice

from apps.accounts.models import User
from apps.hardware.escpos import CUT, DRAWER
from apps.hardware.models import Printer, PrintJob
from apps.hardware.services import enqueue_invoice, enqueue_test, retry_job, save_printer

pytestmark = pytest.mark.django_db


@pytest.fixture
def printer():
    return Printer.objects.create(
        name="Configured output",
        connection_type="TCP",
        address="127.0.0.1",
        cut_paper=False,
        drawer_enabled=False,
    )


def test_output_preferences_persist_and_snapshot_receipt(invoice, actor, printer):
    job = enqueue_invoice(invoice, actor)
    original = bytes(job.payload)
    assert CUT not in original and DRAWER not in original
    printer.cut_paper = True
    save_printer(printer, actor)
    job.refresh_from_db()
    assert bytes(job.payload) == original
    assert enqueue_invoice(invoice, actor).pk == job.pk
    copy = enqueue_invoice(invoice, actor, copy=True, open_drawer=True)
    assert CUT in bytes(copy.payload) and DRAWER not in bytes(copy.payload)
    assert not copy.open_drawer


def test_cash_drawer_can_be_disabled_without_removing_receipt(centre):
    centre.printer.drawer_enabled = False
    centre.printer.save()
    sale = sell(centre)
    job = sale.invoice.print_jobs.get(kind="RECEIPT")
    assert job.kind == "RECEIPT" and not job.open_drawer
    assert DRAWER not in bytes(job.payload)


def test_test_ticket_obeys_cut_and_explicit_drawer_policy(actor, printer):
    job = enqueue_test(printer, actor)
    assert CUT not in bytes(job.payload)
    with pytest.raises(ValidationError, match="deshabilitado"):
        enqueue_test(printer, actor, drawer=True)
    assert PrintJob.objects.count() == 1


@pytest.mark.parametrize("role", ["EMPLOYEE", "MANAGER", "ADMIN"])
def test_device_configuration_service_denies_lower_roles(printer, role):
    actor = User.objects.create_user(username="device-" + role, role=role)
    printer.name = "Unauthorized edit"
    with pytest.raises(PermissionDenied):
        save_printer(printer, actor)
    printer.refresh_from_db()
    assert printer.name == "Configured output"


def test_configurable_output_change_audited_and_inflight_target_protected(actor, printer):
    from apps.audit.models import AuditEvent

    job = enqueue_test(printer, actor)
    PrintJob.objects.filter(pk=job.pk).update(status="SENDING")
    printer.address = "127.0.0.2"
    with pytest.raises(ValidationError, match="entrega en curso"):
        save_printer(printer, actor)
    printer.refresh_from_db()
    assert printer.address == "127.0.0.1"
    PrintJob.objects.filter(pk=job.pk).update(status="UNKNOWN")
    printer.enabled = False
    save_printer(printer, actor)
    assert AuditEvent.objects.filter(action="device.saved").exists()
    with pytest.raises(ValidationError, match="incierta"):
        retry_job(job, actor)


def test_stale_enabled_printer_cannot_create_or_reroute_work(actor, printer):
    job = enqueue_test(printer, actor)
    Printer.objects.filter(pk=printer.pk).update(enabled=False)
    with pytest.raises(ValidationError, match="deshabilitado"):
        enqueue_test(printer, actor)
    with pytest.raises(ValidationError, match="deshabilitado"):
        retry_job(job, actor, printer=printer)
