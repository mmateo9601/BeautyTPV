"""SQLite online backup, authenticated encryption and strictly offline recovery."""

import base64
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet

from .versioning import application_version


def backup_key():
    value = os.environ.get("BEAUTYTPV_BACKUP_KEY", "")
    if not value:
        raise ValueError(
            "Configure BEAUTYTPV_BACKUP_KEY fuera del repositorio; use Fernet.generate_key()."
        )
    return value.encode()


def backup_directory():
    from django.conf import settings

    return Path(
        os.environ.get("BEAUTYTPV_BACKUP_DIR", str(settings.BASE_DIR / "backups"))
    ).resolve()


def hold_path(database):
    return Path(str(database) + ".fiscal-restore-hold")


@contextmanager
def service_lock(database, *, exclusive=False):
    """Cross-process shared service / exclusive maintenance lifecycle lock."""
    lock = Path(str(database) + ".service.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    stream = lock.open("a+b")
    windows_overlapped = None
    windows_api = None
    try:
        if os.name == "nt":
            import ctypes
            import msvcrt
            from ctypes import wintypes

            class Overlapped(ctypes.Structure):
                _fields_ = [
                    ("Internal", ctypes.c_size_t),
                    ("InternalHigh", ctypes.c_size_t),
                    ("Offset", wintypes.DWORD),
                    ("OffsetHigh", wintypes.DWORD),
                    ("hEvent", wintypes.HANDLE),
                ]

            windows_api = ctypes.WinDLL("kernel32", use_last_error=True)
            windows_api.LockFileEx.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(Overlapped),
            ]
            windows_api.LockFileEx.restype = wintypes.BOOL
            windows_api.UnlockFileEx.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(Overlapped),
            ]
            windows_api.UnlockFileEx.restype = wintypes.BOOL
            windows_overlapped = Overlapped()
            flags = 1 | (2 if exclusive else 0)
            if not windows_api.LockFileEx(
                msvcrt.get_osfhandle(stream.fileno()),
                flags,
                0,
                1,
                0,
                ctypes.byref(windows_overlapped),
            ):
                raise OSError(ctypes.get_last_error(), "LockFileEx")
        else:
            import fcntl

            fcntl.flock(
                stream.fileno(), (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB
            )
    except OSError:
        stream.close()
        raise RuntimeError(
            "Servicio o mantenimiento activo. Detenga BeautyTPV y todos los workers antes de restaurar/actualizar."
        ) from None
    try:
        yield
    finally:
        if os.name == "nt":
            import ctypes
            import msvcrt

            windows_api.UnlockFileEx(
                msvcrt.get_osfhandle(stream.fileno()), 0, 1, 0, ctypes.byref(windows_overlapped)
            )
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


@contextmanager
def exclusive_operation(database):
    with service_lock(database, exclusive=True):
        yield


def create_backup(database, destination, key):
    database = Path(database).resolve()
    destination = Path(destination).resolve()
    if not database.is_file():
        raise ValueError("Base SQLite no encontrada.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError("La copia destino ya existe; no se sobrescribe.")
    with tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory) / "snapshot.sqlite3"
        source = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
        target = sqlite3.connect(snapshot)
        try:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Integridad de backup inválida.")
            migrations = target.execute(
                "SELECT app,name FROM django_migrations ORDER BY app,name"
            ).fetchall()
            watermarks = {}
            for table in [
                "billing_invoice",
                "verifactu_fiscalrecord",
                "verifactu_fiscaltransmission",
            ]:
                try:
                    watermarks[table] = target.execute(f"SELECT MAX(id) FROM {table}").fetchone()[0]
                except sqlite3.OperationalError:
                    watermarks[table] = None
        finally:
            target.close()
            source.close()
        payload = snapshot.read_bytes()
        manifest = {
            "format": 1,
            "software": "BeautyTPV",
            "version": application_version(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database_sha256": hashlib.sha256(payload).hexdigest(),
            "migrations": migrations,
            "fiscal_watermarks": watermarks,
        }
        envelope = json.dumps(
            {"manifest": manifest, "database": base64.b64encode(payload).decode()}
        ).encode()
        encrypted = Fernet(key).encrypt(envelope)
        temporary = destination.with_name(destination.name + ".partial")
        with temporary.open("xb") as output:
            output.write(encrypted)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
        return manifest, hashlib.sha256(encrypted).hexdigest()


def inspect_backup(archive, key):
    envelope = json.loads(Fernet(key).decrypt(Path(archive).read_bytes()))
    manifest = envelope["manifest"]
    payload = base64.b64decode(envelope["database"], validate=True)
    if (
        manifest.get("format") != 1
        or hashlib.sha256(payload).hexdigest() != manifest["database_sha256"]
    ):
        raise ValueError("Manifest o hash de copia inválido.")
    return manifest, payload


def restore_backup(archive, database, key, *, confirmation, offline=False):
    if confirmation != "RESTORE OFFLINE" or not offline:
        raise ValueError("Restauración requiere --offline y confirmación RESTORE OFFLINE.")
    database = Path(database).resolve()
    manifest, payload = inspect_backup(archive, key)
    database.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_operation(database):
        with tempfile.NamedTemporaryFile(
            dir=database.parent, suffix=".restore", delete=False
        ) as output:
            staged = Path(output.name)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        try:
            connection = sqlite3.connect(staged)
            try:
                if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("La copia no supera integrity_check.")
            finally:
                connection.close()
            if database.exists():
                recovery = Path(
                    str(database)
                    + ".before-restore-"
                    + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
                    + ".btpv"
                )
                create_backup(database, recovery, key)
            hold_path(database).write_text(
                json.dumps(
                    {
                        "reason": "Restauración: reconciliar registros y acuses AEAT antes de reanudar",
                        "manifest": manifest,
                    }
                ),
                encoding="utf-8",
            )
            # All processes must be stopped: sidecars cannot survive the database swap.
            for suffix in ["-wal", "-shm"]:
                sidecar = Path(str(database) + suffix)
                if sidecar.exists():
                    sidecar.unlink()
            os.replace(staged, database)
        finally:
            if staged.exists():
                staged.unlink()
    return manifest
