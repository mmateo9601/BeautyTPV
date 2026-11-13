"""Audit regression tests; sockets use loopback only, never a physical printer."""

import base64
import json
import socket
import threading
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import Invoice, InvoiceLine
from apps.core.models import Terminal
from apps.hardware.agent import run_once, validate_server, write_journal
from apps.hardware.drivers import send
from apps.hardware.escpos import render_receipt
from apps.hardware.models import HardwareEvent, Printer, PrintJob
from apps.hardware.services import (
    enqueue_invoice,
    enqueue_test,
    process_job,
    recover_expired,
    retry_job,
)

pytestmark = pytest.mark.django_db
TOKEN = "audit-bridge-token-" + "7" * 48


@pytest.fixture
def setup(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    actor = User.objects.create_user(username="audit-hardware", role="SUPERADMIN")
    terminal = Terminal(code="hw-audit", name="Terminal audit")
    terminal.set_bridge_token(TOKEN)
    terminal.save()
    printer = Printer.objects.create(
        name="Remote audit",
        terminal=terminal,
        connection_type="TCP",
        address="127.0.0.1",
        port=9100,
    )
    return actor, terminal, printer


@pytest.fixture
def invoice(setup):
    actor, _, _ = setup
    invoice = Invoice.objects.create(
        series="HA",
        year=2026,
        number=1,
        invoice_type="F1",
        issued_at=timezone.now(),
        issuer={
            "name": "Test issuer",
            "tax_id": "89890001K",
            "address": "Test street",
            "timezone": "Europe/Madrid",
        },
        customer={"name": "Customer test", "tax_id": "89890001K", "address": "Customer street"},
        total="12.10",
        net_total="10",
        tax_total="2.10",
        created_by=actor,
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        description="Test service",
        quantity=1,
        unit_price="12.10",
        discount_percent=0,
        tax_rate=21,
        net_total="10",
        tax_total="2.10",
        total="12.10",
    )
    invoice.refresh_from_db()
    return invoice


def auth():
    return {"HTTP_AUTHORIZATION": "Bearer " + TOKEN}


def claim_path(terminal):
    return f"/hardware/bridge/{terminal.pk}/claim/"


def ack_path(terminal, job):
    return f"/hardware/bridge/{terminal.pk}/jobs/{job.pk}/ack/"


def test_tcp_loopback_transmits_exact_bytes_without_physical_device():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(3)
    received = []

    def consume():
        try:
            connection, _ = server.accept()
        except OSError:
            return
        with connection:
            data = b""
            while True:
                fragment = connection.recv(4096)
                if not fragment:
                    break
                data += fragment
            received.append(data)

    worker = threading.Thread(target=consume)
    worker.start()
    payload = b"\x1b@Test receipt\n\x1dV\x00"
    try:
        assert send(
            SimpleNamespace(
                connection_type="TCP", address="127.0.0.1", port=server.getsockname()[1]
            ),
            payload,
        ) == len(payload)
        worker.join(4)
        assert not worker.is_alive()
        assert received == [payload]
    finally:
        server.close()
        worker.join(1)


@pytest.mark.parametrize(
    "field,value",
    [("encoding", "not-a-codec"), ("codepage", 256), ("port", 70000), ("address", "")],
)
def test_invalid_device_configuration_rejected(setup, field, value):
    printer = setup[2]
    setattr(printer, field, value)
    with pytest.raises(ValidationError):
        printer.full_clean()


def test_invalid_device_does_not_roll_back_invoice_spooling(setup, invoice):
    actor, _, printer = setup
    printer.terminal = None
    printer.codepage = 999
    printer.save()
    job = enqueue_invoice(invoice, actor)
    assert job.status == "PENDING" and job.printer_id is None
    assert "invalida" in job.last_error
    assert invoice.print_jobs.count() == 1


def test_full_receipt_contains_customer_and_rectification_reference(setup, invoice):
    data = render_receipt(invoice)
    assert b"Customer test" in data and b"Customer street" in data
    invoice.rectifies_id = invoice.pk
    invoice.rectifies = invoice
    invoice.reason = "Total refund test"
    data = render_receipt(invoice)
    assert b"Rectifica: " + invoice.full_number.encode() in data
    assert b"Total refund test" in data


def test_print_intent_and_hardware_events_cannot_be_changed_by_queryset(setup, invoice):
    job = enqueue_invoice(invoice, setup[0])
    with pytest.raises(IntegrityError), transaction.atomic():
        PrintJob.objects.filter(pk=job.pk).update(open_drawer=True, payload=b"replacement")
    event = HardwareEvent.objects.filter(job=job).first()
    with pytest.raises(IntegrityError), transaction.atomic():
        HardwareEvent.objects.filter(pk=event.pk).update(action="DONE")


def test_lease_expired_during_send_is_not_falsely_reported_done(setup):
    actor, _, printer = setup
    printer.terminal = None
    printer.save()
    job = enqueue_test(printer, actor)

    def finish_after_expiry(*args):
        PrintJob.objects.filter(pk=job.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
        recover_expired()

    with patch("apps.hardware.services.send", side_effect=finish_after_expiry):
        assert process_job(job.pk) is False
    job.refresh_from_db()
    assert job.status == "UNKNOWN"
    assert not HardwareEvent.objects.filter(job=job, action="DONE").exists()


def test_retry_different_encoding_is_rejected(setup):
    actor, _, printer = setup
    job = enqueue_test(printer, actor)
    replacement = Printer.objects.create(
        name="Different encoding",
        connection_type="TCP",
        address="127.0.0.1",
        encoding="cp437",
        codepage=0,
    )
    with pytest.raises(ValidationError):
        retry_job(job, actor, printer=replacement)


def test_bridge_claim_ack_are_token_scoped_and_idempotent(setup):
    actor, terminal, printer = setup
    job = enqueue_test(printer, actor)
    client = Client(enforce_csrf_checks=True)
    assert client.post(claim_path(terminal)).status_code == 403
    response = client.post(claim_path(terminal), **auth())
    assert response.status_code == 200
    payload = response.json()
    assert base64.b64decode(payload["payload"]) == bytes(job.payload)
    assert payload["printer"]["address"] == "127.0.0.1"
    assert client.post(claim_path(terminal), **auth()).status_code == 204
    other = Terminal(code="other", name="Other")
    other.set_bridge_token(TOKEN)
    other.save()
    assert (
        client.post(
            ack_path(other, job),
            json.dumps({"status": "DONE", "lease_token": payload["lease_token"]}),
            content_type="application/json",
            **auth(),
        ).status_code
        == 403
    )
    packet = {"status": "DONE", "lease_token": payload["lease_token"]}
    assert (
        client.post(
            ack_path(terminal, job), json.dumps(packet), content_type="application/json", **auth()
        ).status_code
        == 200
    )
    assert (
        client.post(
            ack_path(terminal, job), json.dumps(packet), content_type="application/json", **auth()
        ).json()["duplicate_ack"]
        is True
    )
    job.refresh_from_db()
    assert job.status == "DONE" and job.attempts == 1
    assert HardwareEvent.objects.filter(job=job, action="DONE").count() == 1


def test_bridge_expired_delivery_is_quarantined_and_remote_jobs_not_locally_sent(setup):
    actor, terminal, printer = setup
    job = enqueue_test(printer, actor)
    assert not process_job(job.pk)
    client = Client()
    packet = client.post(claim_path(terminal), **auth()).json()
    PrintJob.objects.filter(pk=job.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
    assert client.post(claim_path(terminal), **auth()).status_code == 204
    assert (
        client.post(
            ack_path(terminal, job),
            json.dumps({"status": "DONE", "lease_token": packet["lease_token"]}),
            content_type="application/json",
            **auth(),
        ).status_code
        == 409
    )
    job.refresh_from_db()
    assert job.status == "UNKNOWN"


def test_bridge_restore_hold_prevents_claim(setup):
    actor, terminal, printer = setup
    job = enqueue_test(printer, actor)
    with patch("apps.hardware.bridge.require_operational", side_effect=ValidationError("held")):
        assert Client().post(claim_path(terminal), **auth()).status_code == 503
    job.refresh_from_db()
    assert job.status == "PENDING" and job.attempts == 0


def test_test_and_retry_endpoints_require_technical_authorization(setup):
    actor, _, printer = setup
    client = Client()
    client.force_login(actor)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    job = enqueue_test(printer, actor)
    assert client.post(f"/hardware/impresoras/{printer.pk}/prueba/").status_code == 403
    assert client.post(f"/hardware/trabajos/{job.pk}/reintentar/").status_code == 403


class DjangoTransport:
    def __init__(self):
        self.client = Client()

    def post(self, url, headers=None, json=None, timeout=None):
        from urllib.parse import urlsplit

        response = self.client.post(
            urlsplit(url).path,
            data=__import__("json").dumps(json or {}),
            content_type="application/json",
            HTTP_AUTHORIZATION=headers["Authorization"],
        )
        result = SimpleNamespace(status_code=response.status_code, json=response.json)

        def raise_for_status():
            if response.status_code >= 400:
                raise requests.HTTPError(str(response.status_code))

        result.raise_for_status = raise_for_status
        return result


def test_remote_agent_complete_claim_print_ack_and_restart_safety(setup, tmp_path):
    actor, terminal, printer = setup
    job = enqueue_test(printer, actor)
    sender = Mock()
    journal = tmp_path / "agent.json"
    assert (
        run_once(DjangoTransport(), "https://tpv.test", terminal.pk, TOKEN, journal, sender)
        == "DONE"
    )
    assert sender.call_count == 1 and not journal.exists()
    job.refresh_from_db()
    assert job.status == "DONE"
    interrupted = enqueue_test(printer, actor, drawer=True)
    claimed = Client().post(claim_path(terminal), **auth()).json()
    write_journal(
        journal,
        {
            "server": "https://tpv.test",
            "terminal": terminal.pk,
            "job_id": interrupted.pk,
            "lease_token": claimed["lease_token"],
            "status": None,
        },
    )
    assert (
        run_once(DjangoTransport(), "https://tpv.test", terminal.pk, TOKEN, journal, sender)
        == "UNKNOWN"
    )
    assert sender.call_count == 1
    interrupted.refresh_from_db()
    assert interrupted.status == "UNKNOWN"


@pytest.mark.parametrize(
    "server", ["http://tpv.local", "https://user:secret@tpv.local", "https://tpv.local/?token=x"]
)
def test_agent_rejects_unsafe_server_urls(server):
    with pytest.raises(ValueError):
        validate_server(server)
    assert validate_server("http://127.0.0.1:8000", True) == "http://127.0.0.1:8000"


def test_terminal_routing_prefers_its_device_and_has_explicit_local_fallback(setup, invoice):
    from apps.pos.models import OpenTicket, Sale

    actor, terminal, remote = setup
    local = Printer.objects.create(
        name="Local fallback", connection_type="TCP", address="127.0.0.1"
    )
    ticket = OpenTicket.objects.create(created_by=actor, terminal=terminal)
    sale = Sale.objects.create(
        ticket=ticket,
        total="12.10",
        created_by=actor,
        idempotency_key="hardware-route",
        request_fingerprint="a" * 64,
    )
    invoice.sale = sale
    first = enqueue_invoice(invoice, actor)
    assert first.printer_id == remote.pk
    remote.enabled = False
    remote.save(update_fields=["enabled"])
    copy = enqueue_invoice(invoice, actor, copy=True)
    assert copy.printer_id == local.pk


def test_agent_ack_network_failure_retries_ack_without_reprinting(setup, tmp_path):
    actor, terminal, printer = setup
    job = enqueue_test(printer, actor)
    sender = Mock()
    transport = DjangoTransport()
    original = transport.post

    def lose_ack(url, **kwargs):
        response = original(url, **kwargs)
        if url.endswith("/ack/"):
            raise requests.ConnectionError("Response lost after server committed")
        return response

    transport.post = lose_ack
    journal = tmp_path / "agent-lost-ack.json"
    with pytest.raises(requests.ConnectionError):
        run_once(transport, "https://tpv.test", terminal.pk, TOKEN, journal, sender)
    assert sender.call_count == 1 and journal.exists()
    job.refresh_from_db()
    assert job.status == "DONE"
    assert (
        run_once(DjangoTransport(), "https://tpv.test", terminal.pk, TOKEN, journal, sender)
        == "DONE"
    )
    assert sender.call_count == 1 and not journal.exists()


def test_sql_replace_cannot_replace_print_intent_or_hardware_history(setup):
    from django.db import connection

    job = enqueue_test(setup[2], setup[0])
    event = HardwareEvent.objects.create(job=job, printer=setup[2], action="TEST_EVENT")
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO hardware_hardwareevent (id,job_id,printer_id,action,message,created_at) SELECT id,job_id,printer_id, %s, message,created_at FROM hardware_hardwareevent WHERE id=%s",
            ["FORGED", event.pk],
        )
    columns = [field.column for field in PrintJob._meta.concrete_fields]
    names = ", ".join(columns)
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            f"INSERT OR REPLACE INTO hardware_printjob ({names}) SELECT {names} FROM hardware_printjob WHERE id=%s",
            [job.pk],
        )


def test_multibyte_encoding_cannot_turn_customer_unicode_into_drawer_commands():
    import pytest
    from django.core.exceptions import ValidationError

    from apps.hardware.models import Printer

    printer = Printer(
        name="UTF16 unsafe", connection_type="TCP", address="127.0.0.1", encoding="utf-16le"
    )
    with pytest.raises(ValidationError):
        printer.full_clean(exclude=["terminal"])
