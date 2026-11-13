import hashlib
import json
import sqlite3
import zipfile

import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.test import Client
from django.utils import timezone

from apps.support.operations import (
    create_backup,
    exclusive_operation,
    hold_path,
    inspect_backup,
    restore_backup,
    service_lock,
)
from apps.support.updates import apply_update, validate_package


def database(path):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE django_migrations (app TEXT,name TEXT)")
    connection.execute("INSERT INTO django_migrations VALUES ('core','0001_initial')")
    connection.execute("CREATE TABLE sale (id INTEGER PRIMARY KEY,total TEXT)")
    connection.execute("INSERT INTO sale VALUES (1,'24.20')")
    connection.commit()
    connection.close()
    return path


def archive(tmp_path, files=None, version="0.2.0"):
    files = files or {"manage.py": b"print('updated')"}
    path = tmp_path / "release.zip"
    manifest = {
        "version": version,
        "files": {name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()},
    }
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("release.json", json.dumps(manifest))
        for name, payload in files.items():
            package.writestr(name, payload)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_backup_encrypted_integrity_and_restore(tmp_path):
    original = database(tmp_path / "source.sqlite3")
    key = Fernet.generate_key()
    copy = tmp_path / "backup.btpv"
    manifest, digest = create_backup(original, copy, key)
    assert b"SQLite format" not in copy.read_bytes()
    assert digest == hashlib.sha256(copy.read_bytes()).hexdigest()
    assert manifest["migrations"] == [("core", "0001_initial")]
    restored = tmp_path / "restored.sqlite3"
    restore_backup(copy, restored, key, confirmation="RESTORE OFFLINE", offline=True)
    assert sqlite3.connect(restored).execute("SELECT total FROM sale").fetchone() == ("24.20",)
    assert hold_path(restored).exists()
    assert inspect_backup(copy, key)[0]["database_sha256"] == manifest["database_sha256"]


def test_backup_tamper_and_wrong_key_rejected(tmp_path):
    source = database(tmp_path / "db.sqlite3")
    copy = tmp_path / "copy.btpv"
    key = Fernet.generate_key()
    create_backup(source, copy, key)
    with pytest.raises(InvalidToken):
        inspect_backup(copy, Fernet.generate_key())
    payload = bytearray(copy.read_bytes())
    payload[60] ^= 1
    copy.write_bytes(payload)
    with pytest.raises(InvalidToken):
        inspect_backup(copy, key)


def test_backup_never_overwrites_existing_copy(tmp_path):
    source = database(tmp_path / "db.sqlite3")
    copy = tmp_path / "copy.btpv"
    key = Fernet.generate_key()
    create_backup(source, copy, key)
    with pytest.raises(ValueError):
        create_backup(source, copy, key)


def test_restore_requires_offline_confirmation_and_retains_current(tmp_path):
    source = database(tmp_path / "db.sqlite3")
    copy = tmp_path / "copy.btpv"
    key = Fernet.generate_key()
    create_backup(source, copy, key)
    with pytest.raises(ValueError):
        restore_backup(copy, source, key, confirmation="RESTORE OFFLINE")
    with pytest.raises(ValueError):
        restore_backup(copy, source, key, confirmation="yes", offline=True)
    restore_backup(copy, source, key, confirmation="RESTORE OFFLINE", offline=True)
    assert len(list(tmp_path.glob("*.before-restore-*.btpv"))) == 1


def test_service_shared_maintenance_exclusive(tmp_path):
    path = tmp_path / "db.sqlite3"
    with service_lock(path), service_lock(path):
        with pytest.raises(RuntimeError):
            with exclusive_operation(path):
                pass
    with exclusive_operation(path):
        with pytest.raises(RuntimeError):
            with service_lock(path):
                pass


def test_restore_rejects_running_service(tmp_path):
    source = database(tmp_path / "db.sqlite3")
    copy = tmp_path / "copy.btpv"
    key = Fernet.generate_key()
    create_backup(source, copy, key)
    with service_lock(source), pytest.raises(RuntimeError):
        restore_backup(copy, source, key, confirmation="RESTORE OFFLINE", offline=True)
    assert not hold_path(source).exists()


def test_update_validates_hash_and_paths(tmp_path):
    package, digest = archive(tmp_path)
    assert validate_package(package, digest)["version"] == "0.2.0"
    with pytest.raises(ValueError):
        validate_package(package, "0" * 64)
    package, digest = archive(tmp_path, {"../manage.py": b"bad"})
    with pytest.raises(ValueError):
        validate_package(package, digest)
    package, digest = archive(tmp_path, {".env": b"bad"})
    with pytest.raises(ValueError):
        validate_package(package, digest)


def test_update_migrates_without_rollback_database(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    db = database(root / "db.sqlite3")
    (root / "manage.py").write_text("old")
    package, digest = archive(tmp_path)
    calls = []
    apply_update(
        package,
        digest,
        root,
        db,
        Fernet.generate_key(),
        offline=True,
        runner=lambda args: calls.append(args),
    )
    assert (root / "manage.py").read_text() == "print('updated')"
    assert [args[-1] for args in calls] == ["--noinput", "check", "--noinput"]
    assert sqlite3.connect(db).execute("SELECT total FROM sale").fetchone() == ("24.20",)


def test_failed_update_rolls_code_back_and_holds_operation(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    db = database(root / "db.sqlite3")
    (root / "manage.py").write_text("old")
    package, digest = archive(tmp_path)

    def fail(args):
        connection = sqlite3.connect(db)
        connection.execute("INSERT INTO sale VALUES (2,'10.00')")
        connection.commit()
        connection.close()
        raise RuntimeError("migration failed")

    with pytest.raises(RuntimeError):
        apply_update(package, digest, root, db, Fernet.generate_key(), offline=True, runner=fail)
    assert (root / "manage.py").read_text() == "old"
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM sale").fetchone() == (2,)
    assert hold_path(db).exists()


@pytest.mark.django_db
def test_support_requires_superadmin_and_elevation():
    from apps.accounts.models import User

    user = User.objects.create_user(username="employee", role="EMPLOYEE")
    client = Client()
    client.force_login(user)
    assert client.get("/soporte/").status_code == 403
    user.role = "SUPERADMIN"
    user.save()
    assert client.get("/soporte/").status_code == 403
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    assert client.get("/soporte/").status_code == 200
    assert client.post("/soporte/backup/").status_code == 403


@pytest.mark.django_db
def test_support_authorization_scope_expiry_and_pii_separation():
    from django.core.exceptions import PermissionDenied

    from apps.accounts.models import User
    from apps.support.services import authorize_support, require_authorization

    user = User.objects.create_user(
        username="technician", password="not-a-default-very-long-password", role="SUPERADMIN"
    )
    authorization = authorize_support(
        user,
        user.username,
        "not-a-default-very-long-password",
        "Diagnóstico autorizado",
        origin="test",
    )
    assert authorization.active
    assert require_authorization(user).pk == authorization.pk
    with pytest.raises(PermissionDenied):
        require_authorization(user, "BACKUP")
    with pytest.raises(PermissionDenied):
        authorize_support(
            user,
            user.username,
            "not-a-default-very-long-password",
            "Revisión PII",
            "PII",
            origin="test",
        )
    authorization.expires_at = timezone.now()
    authorization.save()
    with pytest.raises(PermissionDenied):
        require_authorization(user)


@pytest.mark.django_db
def test_admin_cannot_create_superadmin_via_team_ui():
    from apps.accounts.models import User

    user = User.objects.create_user(username="administrator", role="ADMIN")
    client = Client()
    client.force_login(user)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    response = client.post(
        "/usuarios/",
        {"username": "attacker", "role": "SUPERADMIN", "password": "verylongpassword123"},
    )
    assert response.status_code == 200
    assert not User.objects.filter(username="attacker").exists()


def test_cross_process_worker_blocks_restore(tmp_path):
    import subprocess
    import sys

    path = tmp_path / "db.sqlite3"
    code = "from apps.support.operations import service_lock; import sys; guard=service_lock(sys.argv[1]); guard.__enter__(); print('LOCKED',flush=True); sys.stdin.readline(); guard.__exit__(None,None,None)"
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout.readline().strip() == "LOCKED"
        with pytest.raises(RuntimeError):
            with exclusive_operation(path):
                pass
        process.communicate("stop\n", timeout=5)
        assert process.returncode == 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
