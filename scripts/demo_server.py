"""Loopback-only DEMO host: Waitress, simulated printing and cooperative Windows stop.

This entry point deliberately never starts the fiscal/operations worker. Its
network audit hook is installed only in this dedicated process, never in the
normal application or production service.
"""

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TOKEN_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_network_guard_installed = False


def event_name(token):
    if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
        raise ValueError("La identidad de ejecución DEMO no es válida.")
    return "Local\\BeautyTPV-DEMO-" + token


class WindowsEvent:
    """A per-execution named event; no process termination or process-name search."""

    def __init__(self, token, *, create=True):
        if os.name != "nt":
            raise RuntimeError("La ejecución DEMO por acceso directo requiere Windows.")
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._api = ctypes.WinDLL("kernel32", use_last_error=True)
        self._api.CreateEventW.argtypes = [
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        self._api.CreateEventW.restype = wintypes.HANDLE
        self._api.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        self._api.OpenEventW.restype = wintypes.HANDLE
        self._api.SetEvent.argtypes = [wintypes.HANDLE]
        self._api.SetEvent.restype = wintypes.BOOL
        self._api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._api.WaitForSingleObject.restype = wintypes.DWORD
        self._api.CloseHandle.argtypes = [wintypes.HANDLE]
        self._api.CloseHandle.restype = wintypes.BOOL
        name = event_name(token)
        if create:
            self.handle = self._api.CreateEventW(None, True, False, name)
            error = ctypes.get_last_error()
            if self.handle and error == 183:  # ERROR_ALREADY_EXISTS
                self.close()
                raise RuntimeError("La señal de esta ejecución DEMO ya existe.")
        else:
            # EVENT_MODIFY_STATE | SYNCHRONIZE, rather than unrestricted access.
            self.handle = self._api.OpenEventW(0x0002 | 0x00100000, False, name)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def set(self):
        if not self.handle or not self._api.SetEvent(self.handle):
            raise self._ctypes.WinError(self._ctypes.get_last_error())

    def wait(self, timeout=0):
        if not self.handle:
            raise RuntimeError("La señal DEMO ya está cerrada.")
        if timeout is None:
            milliseconds = 0xFFFFFFFF
        elif not isinstance(timeout, (int, float)) or not 0 <= timeout <= 86400:
            raise ValueError("Tiempo de espera no válido.")
        else:
            milliseconds = int(timeout * 1000)
        result = self._api.WaitForSingleObject(self.handle, milliseconds)
        if result == 0:
            return True
        if result == 258:  # WAIT_TIMEOUT
            return False
        raise self._ctypes.WinError(self._ctypes.get_last_error())

    def close(self):
        handle = getattr(self, "handle", None)
        if handle:
            self._api.CloseHandle(handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _loopback_host(host):
    if isinstance(host, bytes):
        host = host.decode("ascii", errors="replace")
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        return False


def network_audit(event, arguments):
    """Reject DNS lookup/connect outside loopback before network IO can occur."""
    if event == "socket.getaddrinfo":
        host = arguments[0]
    elif event == "socket.connect":
        address = arguments[1]
        if not isinstance(address, tuple) or not address:
            raise PermissionError("DEMO: solo se permiten conexiones locales.")
        host = address[0]
    else:
        return
    if not _loopback_host(host):
        raise PermissionError("DEMO sin conexiones externas ni remisiones AEAT.")


def install_network_guard():
    global _network_guard_installed
    if not _network_guard_installed:
        sys.addaudithook(network_audit)
        _network_guard_installed = True


class DemoIdentityApplication:
    """Private readiness handshake, separate from the application's health URL."""

    def __init__(self, application, token):
        event_name(token)
        self.application = application
        self.token = token
        self.identity = hashlib.sha256(token.encode("ascii")).hexdigest()

    def __call__(self, environ, start_response):
        if not _loopback_host(environ.get("REMOTE_ADDR", "")):
            start_response("403 Forbidden", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"DEMO disponible exclusivamente en localhost."]
        if environ.get("PATH_INFO") != "/__demo_ready__":
            return self.application(environ, start_response)
        supplied = environ.get("HTTP_X_BEAUTYTPV_DEMO", "")
        if (
            environ.get("REQUEST_METHOD") != "GET"
            or not isinstance(supplied, str)
            or not TOKEN_PATTERN.fullmatch(supplied)
            or not hmac.compare_digest(supplied, self.token)
        ):
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"Not found"]
        payload = json.dumps(
            {"demo": True, "pid": os.getpid(), "identity": self.identity, "mode": "TEST"}
        ).encode("utf-8")
        start_response(
            "200 OK",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [payload]


def validate_demo_profile(settings, instance_dir):
    """Check immutable process configuration before touching application data."""
    directory = Path(instance_dir).resolve(strict=True)
    database = Path(settings.DATABASES["default"]["NAME"]).resolve(strict=True)
    if (
        settings.SETTINGS_MODULE != "config.demo_settings"
        or not getattr(settings, "LOCAL_DEMO_ONLY", False)
        or settings.DEBUG
        or not getattr(settings, "HARDWARE_SIMULATOR", False)
        or database.parent != directory
        or database == ROOT / "db.sqlite3"
        or not database.is_file()
    ):
        raise ValueError("El servidor solo admite la configuración y SQLite aislada DEMO.")
    if (
        settings.FISCAL_ENVIRONMENT != "TEST"
        or settings.FISCAL_PRODUCTION_APPROVED
        or not getattr(settings, "FISCAL_RESTORE_HOLD", False)
        or settings.AEAT_CERTIFICATE
        or settings.AEAT_PRIVATE_KEY
    ):
        raise ValueError("DEMO exige TEST, remisión bloqueada y certificados vacíos.")
    return database


def validate_demo_database(instance_dir):
    """Fail closed before serving if a different profile/database is selected."""
    from django.conf import settings

    from apps.core.models import CompanySettings
    from apps.hardware.models import Printer
    from apps.support.models import TechnicalSettings

    validate_demo_profile(settings, instance_dir)
    company = CompanySettings.objects.filter(pk=1).first()
    technical = TechnicalSettings.objects.filter(pk=1).first()
    if (
        company is None
        or company.fiscal_mode != "TEST"
        or technical is None
        or technical.fiscal_environment != "TEST"
        or technical.certificate_path
        or technical.private_key_path
    ):
        raise ValueError("La base DEMO tiene configuración fiscal incompatible; revise la DEMO.")
    if Printer.objects.filter(enabled=True).exclude(connection_type="SIMULATOR").exists():
        raise ValueError("Desactive las impresoras físicas: la DEMO solo admite simulador.")


def run_demo_cycle():
    """Only synthetic print delivery: never invoke the fiscal scheduler."""
    from apps.hardware.models import PrintJob
    from apps.hardware.services import process_job, recover_expired

    recover_expired()
    identifiers = list(
        PrintJob.objects.filter(
            status="PENDING",
            printer__enabled=True,
            printer__terminal__isnull=True,
            printer__connection_type="SIMULATOR",
        ).values_list("pk", flat=True)[:50]
    )
    for identifier in identifiers:
        process_job(identifier)
    return len(identifiers)


def worker_loop(stop, close, *, interval=2, backup_interval=60):
    from django.core.exceptions import ValidationError
    from django.db import close_old_connections, connections

    from apps.support.scheduler import heartbeat, run_backup_policy

    next_backup = 0
    backup_state, backup_error = "RUNNING", "DEMO_NO_FISCAL_TRANSPORT"
    try:
        while not stop.is_set():
            close_old_connections()
            try:
                run_demo_cycle()
                heartbeat("hardware_worker", "RUNNING")
            except ValidationError:
                # Maintenance/restore hold legitimately pauses print jobs.
                heartbeat("hardware_worker", "HELD", "DEMO_MAINTENANCE")
            if time.monotonic() >= next_backup:
                try:
                    run_backup_policy()
                except Exception as error:
                    backup_state, backup_error = "DEGRADED", type(error).__name__
                else:
                    backup_state, backup_error = "RUNNING", "DEMO_NO_FISCAL_TRANSPORT"
                next_backup = time.monotonic() + backup_interval
            # The scheduler is alive between backups too; the UI expires a
            # heartbeat after 30s, independently of the backup interval.
            heartbeat("operations_tasks", backup_state, backup_error)
            heartbeat("service", "RUNNING", "DEMO_LOCALHOST")
            if stop.wait(interval):
                break
    except Exception as error:
        print("DEMO: tarea local detenida (" + type(error).__name__ + ").", flush=True)
        stop.set()
        close()
    finally:
        connections.close_all()


def serve(token, instance_dir):
    import django

    django.setup()
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from waitress import create_server

    from apps.support.operations import service_lock
    from apps.support.scheduler import heartbeat
    from scripts.service import close_server

    validate_demo_database(instance_dir)
    install_network_guard()
    stop = threading.Event()
    worker = monitor = server = None
    with (
        WindowsEvent(token) as signal,
        service_lock(
            Path(instance_dir).resolve() / Path(connections["default"].settings_dict["NAME"]).name
        ),
    ):
        try:
            application = DemoIdentityApplication(get_wsgi_application(), token)
            server = create_server(
                application, host="127.0.0.1", port=8000, threads=4, asyncore_loop_timeout=0.5
            )

            def close():
                try:
                    close_server(server)
                except OSError:
                    pass

            def monitor_signal():
                while not stop.is_set():
                    if signal.wait(0.25):
                        stop.set()
                        close()
                        break

            worker = threading.Thread(
                target=worker_loop, args=(stop, close), name="demo-local-tasks", daemon=True
            )
            monitor = threading.Thread(target=monitor_signal, name="demo-stop-event", daemon=True)
            heartbeat("service", "RUNNING", "DEMO_LOCALHOST")
            worker.start()
            monitor.start()
            print(
                "BeautyTPV DEMO: http://127.0.0.1:8000/acceso/ (solo TEST, sin AEAT).", flush=True
            )
            server.run()
        finally:
            stop.set()
            for thread in (monitor, worker):
                if thread is not None:
                    thread.join(timeout=10)
            if server is not None:
                try:
                    close_server(server)
                except OSError:
                    pass
            try:
                heartbeat("service", "STOPPED", "DEMO_LOCALHOST")
            finally:
                connections.close_all()


def main():
    parser = argparse.ArgumentParser(description="Servidor aislado BeautyTPV DEMO para Windows")
    parser.add_argument("--instance-dir", required=True)
    parser.add_argument("--token", required=True)
    arguments = parser.parse_args()
    event_name(arguments.token)
    directory = Path(arguments.instance_dir).resolve(strict=True)
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.demo_settings"
    os.environ["BEAUTYTPV_DEMO_DIR"] = str(directory)
    try:
        serve(arguments.token, directory)
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        # Logs must never include secrets or raw request/credential material.
        print(
            "No se pudo iniciar BeautyTPV DEMO ("
            + type(error).__name__
            + "). Revise configuración, migraciones y puerto 8000.",
            file=sys.stderr,
            flush=True,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
