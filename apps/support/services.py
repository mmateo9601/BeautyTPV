import platform
import shutil
import socket
import time
from datetime import timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import django
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.accounts.services import authenticate_local
from apps.audit.services import record

from .models import BackupRun, ServiceHeartbeat, SupportSession
from .operations import hold_path
from .versioning import application_version


def authorize_support(
    actor, approver_username, password, justification, scope="TECHNICAL", origin="local"
):
    require_role(actor, "SUPERADMIN")
    if not justification.strip() or scope not in ["TECHNICAL", "PII", "BACKUP", "UPDATE"]:
        raise ValidationError("Motivo y alcance válidos obligatorios.")
    approver = authenticate_local(approver_username, password, origin, password=True)
    if not approver:
        raise PermissionDenied("Aprobación no válida o bloqueada.")
    require_role(approver, "ADMIN")
    if scope == "PII" and approver.pk == actor.pk:
        raise PermissionDenied("Acceso de soporte a PII requiere aprobación de otro administrador.")
    session = SupportSession.objects.create(
        actor=actor,
        approved_by=approver,
        justification=justification[:500],
        scope=scope,
        expires_at=timezone.now() + timedelta(minutes=20),
    )
    record(actor, "support.authorized", obj=session)
    return session


def active_authorization(actor, scope="TECHNICAL"):
    return (
        SupportSession.objects.filter(
            actor=actor,
            actor__is_active=True,
            actor__role="SUPERADMIN",
            scope=scope,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
            approved_by__is_active=True,
            approved_by__role__in=["ADMIN", "SUPERADMIN"],
        )
        .order_by("-id")
        .first()
    )


def require_authorization(actor, scope="TECHNICAL"):
    require_role(actor, "SUPERADMIN")
    session = active_authorization(actor, scope)
    if not session:
        raise PermissionDenied("Autorice una sesión de soporte temporal para esta acción.")
    return session


def diagnostics():
    from apps.hardware.models import PrintJob
    from apps.verifactu.models import FiscalOutbox

    start = time.perf_counter()
    with connection.cursor() as cursor:
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]
        sqlite_version = cursor.execute("SELECT sqlite_version()").fetchone()[0]
    latency = round((time.perf_counter() - start) * 1000, 2)
    migrations = MigrationExecutor(connection).migration_plan(
        MigrationExecutor(connection).loader.graph.leaf_nodes()
    )
    disk = shutil.disk_usage(settings.BASE_DIR)
    from .fiscal import fiscal_configuration

    certificate = fiscal_configuration()["certificate"]
    expiry = "No configurado"
    if certificate:
        try:
            from cryptography import x509

            cert = x509.load_pem_x509_certificate(Path(certificate).read_bytes())
            expiry = cert.not_valid_after_utc.isoformat()
        except (OSError, ValueError):
            expiry = "Certificado no legible/PEM inválido"
    dependencies = {}
    for package in (
        "Django",
        "requests",
        "lxml",
        "Pillow",
        "qrcode",
        "reportlab",
        "cryptography",
        "pyserial",
        "pyusb",
        "waitress",
        "whitenoise",
    ):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            dependencies[package] = "NO INSTALADA"
    return {
        "python_version": platform.python_version(),
        "django_version": django.get_version(),
        "dependencies": dependencies,
        "version": application_version(root=settings.BASE_DIR),
        "workers": {
            item.name: {
                "state": item.state
                if (timezone.now() - item.last_seen).total_seconds() < 30
                else "STALE",
                "last_seen": item.last_seen.isoformat(),
                "pid": item.pid,
                "error_code": item.last_error_code,
            }
            for item in ServiceHeartbeat.objects.all()
        },
        "last_backup": BackupRun.objects.filter(status="COMPLETE")
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first(),
        "sqlite_version": sqlite_version,
        "integrity": integrity,
        "db_latency_ms": latency,
        "disk_free_mb": disk.free // 1048576,
        "pending_migrations": len(migrations),
        "print_pending": PrintJob.objects.filter(
            status__in=["PENDING", "FAILED", "UNKNOWN"]
        ).count(),
        "fiscal_pending": FiscalOutbox.objects.exclude(status__in=["ACCEPTED"]).count(),
        "certificate_expiry": expiry,
        "restore_hold": hold_path(connection.settings_dict["NAME"]).exists(),
        "network": "Conectividad AEAT no medida: ejecutar diagnóstico de red",
    }


def aeat_connectivity():
    started = time.perf_counter()
    try:
        with socket.create_connection(("prewww1.aeat.es", 443), timeout=3):
            pass
        return {
            "reachable": True,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "scope": "TCP 443; no envío fiscal ni autenticación de certificado",
        }
    except OSError:
        return {"reachable": False, "scope": "TCP 443 no disponible"}


def save_terminal(actor, terminal):
    from django.db import transaction

    require_authorization(actor)
    terminal.full_clean()
    with transaction.atomic():
        terminal.save()
        record(actor, "terminal.saved", obj=terminal)
    return terminal


def save_technical_settings(actor, policy):
    from django.db import transaction

    require_authorization(actor)
    policy.full_clean()
    with transaction.atomic():
        policy.save()
        record(actor, "support.settings")
    return policy
