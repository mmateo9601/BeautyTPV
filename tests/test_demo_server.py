"""DEMO host isolation tests. No AEAT request or physical device is used."""

import hashlib
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.demo_server import (
    DemoIdentityApplication,
    WindowsEvent,
    event_name,
    network_audit,
    run_demo_cycle,
    validate_demo_profile,
)


def call_wsgi(application, **changes):
    environment = {
        "REMOTE_ADDR": "127.0.0.1",
        "PATH_INFO": "/__demo_ready__",
        "REQUEST_METHOD": "GET",
    }
    environment.update(changes)
    result = {}

    def start(status, headers):
        result.update(status=status, headers=dict(headers))

    result["body"] = b"".join(application(environment, start))
    return result


def unused_application(environment, start):
    start("200 OK", [("Content-Type", "text/plain")])
    return [b"Application"]


def test_readiness_proves_per_execution_identity_without_disclosing_token():
    token = secrets.token_hex(32)
    application = DemoIdentityApplication(unused_application, token)
    response = call_wsgi(application, HTTP_X_BEAUTYTPV_DEMO=token)
    assert response["status"] == "200 OK"
    assert json.loads(response["body"]) == {
        "demo": True,
        "mode": "TEST",
        "pid": os.getpid(),
        "identity": hashlib.sha256(token.encode("ascii")).hexdigest(),
    }
    assert token.encode() not in response["body"]
    assert response["headers"]["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"HTTP_X_BEAUTYTPV_DEMO": "incorrect"},
        {"HTTP_X_BEAUTYTPV_DEMO": "é" * 64},
        {"REQUEST_METHOD": "POST"},
    ],
)
def test_readiness_rejects_missing_wrong_or_non_ascii_identity(changes):
    token = secrets.token_hex(32)
    response = call_wsgi(DemoIdentityApplication(unused_application, token), **changes)
    assert response["status"] == "404 Not Found"
    assert response["body"] == b"Not found"


def test_loopback_wrapper_passes_application_and_denies_non_local_clients():
    application = DemoIdentityApplication(unused_application, secrets.token_hex(32))
    assert call_wsgi(application, PATH_INFO="/acceso/")["body"] == b"Application"
    assert call_wsgi(application, REMOTE_ADDR="192.0.2.1")["status"] == "403 Forbidden"


@pytest.mark.parametrize("token", ["", "x" * 64, "a" * 63, "a" * 65, "a/../" * 16])
def test_event_identity_rejects_arbitrary_names(token):
    with pytest.raises(ValueError):
        event_name(token)


@pytest.mark.skipif(os.name != "nt", reason="Actual Windows kernel event")
def test_windows_event_signal_is_specific_to_one_execution():
    token, other = secrets.token_hex(32), secrets.token_hex(32)
    with WindowsEvent(token) as owner, WindowsEvent(other) as unrelated:
        assert not owner.wait(0)
        assert not unrelated.wait(0)
        with WindowsEvent(token, create=False) as opener:
            opener.set()
            assert owner.wait(0.5)
            assert not unrelated.wait(0)
        with pytest.raises(RuntimeError):
            WindowsEvent(token)


@pytest.mark.parametrize(
    "event,arguments",
    [
        ("socket.getaddrinfo", ("prewww1.aeat.es", 443)),
        ("socket.getaddrinfo", ("1.1.1.1", 443)),
        ("socket.connect", (None, ("192.0.2.1", 443))),
        ("socket.connect", (None, "arbitrary.sock")),
    ],
)
def test_network_guard_rejects_external_dns_and_connections(event, arguments):
    with pytest.raises(PermissionError):
        network_audit(event, arguments)


def test_installed_audit_hook_blocks_real_socket_api_before_external_dns():
    code = """import socket
from scripts.demo_server import install_network_guard
install_network_guard()
try:
    socket.getaddrinfo('prewww1.aeat.es',443)
except PermissionError:
    print('BLOCKED_BEFORE_DNS')
else:
    raise AssertionError('External DNS was allowed')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "BLOCKED_BEFORE_DNS"
    network_audit("socket.getaddrinfo", ("localhost", 8000))
    network_audit("socket.connect", (None, ("127.0.0.1", 8000)))


@pytest.fixture
def demo_profile(tmp_path):
    database = tmp_path / "demo.sqlite3"
    database.touch()
    return SimpleNamespace(
        SETTINGS_MODULE="config.demo_settings",
        LOCAL_DEMO_ONLY=True,
        DEBUG=False,
        HARDWARE_SIMULATOR=True,
        DATABASES={"default": {"NAME": str(database)}},
        FISCAL_ENVIRONMENT="TEST",
        FISCAL_PRODUCTION_APPROVED=False,
        FISCAL_RESTORE_HOLD=True,
        AEAT_CERTIFICATE="",
        AEAT_PRIVATE_KEY="",
    )


def test_valid_demo_profile_is_isolated_file(demo_profile, tmp_path):
    assert validate_demo_profile(demo_profile, tmp_path) == tmp_path / "demo.sqlite3"


@pytest.mark.parametrize(
    "attribute,value",
    [
        ("SETTINGS_MODULE", "config.settings"),
        ("LOCAL_DEMO_ONLY", False),
        ("DEBUG", True),
        ("HARDWARE_SIMULATOR", False),
        ("FISCAL_ENVIRONMENT", "PRODUCTION"),
        ("FISCAL_PRODUCTION_APPROVED", True),
        ("FISCAL_RESTORE_HOLD", False),
        ("AEAT_CERTIFICATE", "external.pem"),
        ("AEAT_PRIVATE_KEY", "external.key"),
    ],
)
def test_profile_guard_rejects_production_or_missing_isolation(
    demo_profile, tmp_path, attribute, value
):
    setattr(demo_profile, attribute, value)
    with pytest.raises(ValueError):
        validate_demo_profile(demo_profile, tmp_path)


def test_profile_guard_rejects_database_outside_demo(demo_profile, tmp_path):
    wrong = tmp_path / "other"
    wrong.mkdir()
    with pytest.raises(ValueError):
        validate_demo_profile(demo_profile, wrong)


@pytest.mark.django_db
def test_demo_cycle_only_consumes_simulator_and_never_calls_fiscal(monkeypatch, settings):
    from apps.accounts.models import User
    from apps.hardware.models import Printer, PrintJob
    from apps.verifactu.models import FiscalTransmission

    settings.HARDWARE_SIMULATOR = True
    settings.DEBUG = True
    actor = User.objects.create_user(username="demo-cycle")
    simulator = Printer.objects.create(name="Synthetic simulator", connection_type="SIMULATOR")
    physical = Printer.objects.create(name="Unusable physical", connection_type="TCP")
    jobs = []
    for printer in (simulator, physical):
        jobs.append(
            PrintJob.objects.create(
                printer=printer, payload=b"Synthetic", kind="TEST", requested_by=actor
            )
        )
    monkeypatch.setattr(
        "apps.verifactu.services.send_one",
        lambda *args, **kwargs: pytest.fail("DEMO cycle must never send a fiscal record"),
    )
    assert run_demo_cycle() == 1
    jobs[0].refresh_from_db()
    jobs[1].refresh_from_db()
    assert jobs[0].status == "DONE"
    assert jobs[1].status == "PENDING"
    assert not FiscalTransmission.objects.exists()


def test_demo_scheduler_heartbeat_stays_fresh_between_backup_runs(monkeypatch):
    from scripts.demo_server import worker_loop

    records, backups = [], []
    moments = iter((0, 0, 2, 4))
    monkeypatch.setattr("scripts.demo_server.time.monotonic", lambda: next(moments))
    monkeypatch.setattr("scripts.demo_server.run_demo_cycle", lambda: None)
    monkeypatch.setattr("django.db.close_old_connections", lambda: None)
    monkeypatch.setattr("django.db.connections.close_all", lambda: None)
    monkeypatch.setattr("apps.support.scheduler.heartbeat", lambda *args: records.append(args))
    monkeypatch.setattr("apps.support.scheduler.run_backup_policy", lambda: backups.append(1))

    class Stop:
        cycles = 0

        def is_set(self):
            return False

        def wait(self, interval):
            self.cycles += 1
            return self.cycles == 3

        def set(self):
            pytest.fail("The scheduler failed unexpectedly")

    worker_loop(Stop(), lambda: pytest.fail("The server was closed unexpectedly"))
    assert len(backups) == 1
    assert len([record for record in records if record[0] == "operations_tasks"]) == 3
