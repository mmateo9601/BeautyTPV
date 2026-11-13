"""Operational audit regressions: real IO/DB; subprocess execution isolated by explicit runners."""

import hashlib
import json
import sqlite3
import threading
import zipfile
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.utils import timezone

from apps.support import updates
from apps.support.fiscal import validate_certificate_references
from apps.support.forms import PrinterForm, TechnicalSettingsForm, TerminalForm
from apps.support.models import ServiceHeartbeat, SupportSession, TechnicalSettings
from apps.support.operations import hold_path
from apps.support.versioning import application_version


def package(tmp_path, files=None, version="0.2.0"):
    payloads = files or {"manage.py": b"new-code", "apps/new.py": b"new-module"}
    archive = tmp_path / "release.zip"
    manifest = {
        "version": version,
        "files": {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
    }
    with zipfile.ZipFile(archive, "w") as target:
        target.writestr("release.json", json.dumps(manifest))
        for name, payload in payloads.items():
            target.writestr(name, payload)
    return archive, hashlib.sha256(archive.read_bytes()).hexdigest()


def install_root(tmp_path):
    root = tmp_path / "installation"
    root.mkdir()
    (root / "manage.py").write_text("original")
    database = root / "db.sqlite3"
    with sqlite3.connect(database) as conn:
        conn.execute("CREATE TABLE django_migrations (app TEXT,name TEXT)")
    return root, database


def test_partial_file_write_rolls_back_all_code(tmp_path, monkeypatch):
    root, database = install_root(tmp_path)
    archive, digest = package(tmp_path)
    original = updates._atomic_write
    failed = False

    def write_then_fail(destination, payload):
        nonlocal failed
        original(destination, payload)
        if destination.name == "new.py" and not failed:
            failed = True
            raise OSError("simulated disk failure after replace")

    monkeypatch.setattr(updates, "_atomic_write", write_then_fail)
    with pytest.raises(OSError):
        updates.apply_update(
            archive,
            digest,
            root,
            database,
            Fernet.generate_key(),
            offline=True,
            runner=lambda args: None,
        )
    assert (root / "manage.py").read_text() == "original"
    assert not (root / "apps/new.py").exists()
    assert not (root / "release.json").exists()
    assert hold_path(database).exists()
    assert sqlite3.connect(database).execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_preflight_invalid_destination_never_writes_first_file(tmp_path):
    root, database = install_root(tmp_path)
    (root / "apps/new.py").mkdir(parents=True)
    archive, digest = package(tmp_path)
    with pytest.raises(ValueError):
        updates.apply_update(
            archive,
            digest,
            root,
            database,
            Fernet.generate_key(),
            offline=True,
            runner=lambda args: None,
        )
    assert (root / "manage.py").read_text() == "original"
    assert not (root / "backups").exists()


def test_dependency_mismatch_aborts_before_code_and_backup(tmp_path):
    root, database = install_root(tmp_path)
    archive, digest = package(
        tmp_path,
        {"manage.py": b"new-code", "requirements.lock.txt": b"DefinitelyMissingPackage==999.0"},
    )

    def incompatible(args):
        raise RuntimeError("missing dependency")

    with pytest.raises(ValueError, match="Entorno incompatible"):
        updates.apply_update(
            archive,
            digest,
            root,
            database,
            Fernet.generate_key(),
            offline=True,
            runner=incompatible,
        )
    assert (root / "manage.py").read_text() == "original"
    assert not (root / "backups").exists()


def test_update_rejects_case_collision_and_unsafe_version(tmp_path):
    archive, digest = package(tmp_path, {"apps/x.py": b"a", "apps/X.py": b"b"})
    with pytest.raises(ValueError):
        updates.validate_package(archive, digest)
    archive, digest = package(tmp_path, version="../escape")
    with pytest.raises(ValueError):
        updates.validate_package(archive, digest)


def test_release_version_changes_only_after_successful_update(tmp_path):
    root, database = install_root(tmp_path)
    archive, digest = package(tmp_path, version="0.9.8")
    updates.apply_update(
        archive,
        digest,
        root,
        database,
        Fernet.generate_key(),
        offline=True,
        runner=lambda args: None,
    )
    assert application_version(root) == "0.9.8"


def test_supervisor_closes_service_when_child_exits():
    from scripts.service import supervise_workers

    failures = []
    reports = []
    process = SimpleNamespace(pid=321, poll=lambda: 7)
    supervise_workers(
        [("hardware_worker", process)],
        threading.Event(),
        lambda *args: failures.append(args),
        lambda *args: reports.append(args),
    )
    assert failures == [("hardware_worker", 7)]
    assert reports[0][1:3] == ("FAILED", "EXIT_7")


def test_supervisor_reports_monitor_failure():
    from scripts.service import supervise_workers

    failures = []

    def unavailable(*args):
        raise OSError("DB unavailable")

    supervise_workers([], threading.Event(), lambda *args: failures.append(args), unavailable)
    assert failures == [("supervisor", "OSError")]


@pytest.fixture
def certificate_files(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Operational test certificate")])
    now = timezone.now()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    certificate = tmp_path / "certificate.pem"
    private = tmp_path / "private.pem"
    certificate.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return certificate, private


def test_certificate_external_references_validate_key_match(certificate_files):
    certificate, private = certificate_files
    assert validate_certificate_references(str(certificate), str(private))
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private.write_bytes(
        other.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    with pytest.raises(ValidationError, match="no corresponde"):
        validate_certificate_references(str(certificate), str(private))


def test_certificate_must_be_outside_repo(certificate_files, settings):
    certificate, private = certificate_files
    settings.BASE_DIR = certificate.parent
    with pytest.raises(ValidationError):
        validate_certificate_references(str(certificate), str(private))


@pytest.mark.django_db
def test_invalid_backup_policy_rejected():
    form = TechnicalSettingsForm(
        {"backup_retention_days": "0", "backup_interval_hours": "0"},
        instance=TechnicalSettings.load(),
    )
    assert not form.is_valid()
    assert "backup_retention_days" in form.errors and "backup_interval_hours" in form.errors


@pytest.mark.django_db
def test_fiscal_failure_does_not_prevent_backup_task():
    from apps.support.scheduler import run_cycle

    with (
        patch("apps.verifactu.services.send_one", side_effect=OSError("network unavailable")),
        patch("apps.support.scheduler.run_backup_policy") as backup,
    ):
        run_cycle()
    backup.assert_called_once()
    state = ServiceHeartbeat.objects.get(name="operations_tasks")
    assert state.state == "DEGRADED" and state.last_error_code == "FISCAL:OSError"


@pytest.mark.django_db
def test_revoked_approver_invalidates_support_session():
    from apps.accounts.models import User
    from apps.support.services import require_authorization

    actor = User.objects.create_user(username="technician", role="SUPERADMIN")
    approver = User.objects.create_user(username="administrator", role="ADMIN")
    SupportSession.objects.create(
        actor=actor,
        approved_by=approver,
        justification="Support review",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    assert require_authorization(actor)
    approver.is_active = False
    approver.save()
    with pytest.raises(PermissionDenied):
        require_authorization(actor)


@pytest.mark.django_db
def test_terminal_form_hashes_token_and_never_saves_raw_token():
    token = "secret-token-" * 4
    form = TerminalForm(
        {"code": "desk-1", "name": "Reception", "active": "on", "bridge_token": token}
    )
    assert form.is_valid(), form.errors
    terminal = form.save()
    assert token not in terminal.bridge_token_hash
    assert terminal.check_bridge_token(token)


@pytest.mark.django_db
def test_unlock_user_does_not_require_pin_change():
    from apps.accounts.models import LoginThrottle, User
    from apps.accounts.services import _throttle_keys

    admin = User.objects.create_user(username="admin", role="ADMIN")
    employee = User.objects.create_user(username="employee", role="EMPLOYEE")
    employee.set_pin("654321")
    employee.save()
    original_hash = employee.pin_hash
    key = _throttle_keys(employee.username, "")[0]
    LoginThrottle.objects.create(
        key=key, failures=5, locked_until=timezone.now() + timedelta(minutes=10)
    )
    client = Client()
    client.force_login(admin)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    response = client.post(f"/usuarios/{employee.pk}/desbloquear/")
    assert response.status_code == 302
    assert LoginThrottle.objects.get(key=key).failures == 0
    employee.refresh_from_db()
    assert employee.pin_hash == original_hash


@pytest.mark.django_db
def test_printer_form_rejects_unrenderable_encoding_and_invalid_port(settings):
    settings.DEBUG = True
    settings.HARDWARE_SIMULATOR = True
    form = PrinterForm(
        {
            "name": "Broken",
            "connection_type": "TCP",
            "address": "",
            "port": "99999",
            "usb_vendor": 0,
            "usb_product": 0,
            "usb_endpoint": 1,
            "encoding": "unknown-codec",
            "codepage": 19,
            "enabled": "on",
        }
    )
    assert not form.is_valid()
    assert {"address", "port", "encoding"} <= set(form.errors)
