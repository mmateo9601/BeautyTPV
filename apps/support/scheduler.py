"""Independent maintenance tasks: a fiscal outage must not suppress backups."""

import os
from datetime import timedelta
from pathlib import Path

from django.db import connection
from django.utils import timezone

from apps.audit.services import record

from .models import BackupRun, ServiceHeartbeat, TechnicalSettings
from .operations import backup_directory, backup_key, create_backup, hold_path


def heartbeat(name, state="RUNNING", error_code="", pid=None):
    ServiceHeartbeat.objects.update_or_create(
        name=name,
        defaults={
            "pid": pid or os.getpid(),
            "state": state,
            "last_seen": timezone.now(),
            "last_error_code": error_code[:100],
        },
    )


def run_backup_policy():
    policy = TechnicalSettings.load()
    if policy.backup_interval_hours < 1 or policy.backup_retention_days < 1:
        raise ValueError("Política de backup inválida: intervalo/retención deben ser positivos.")
    latest = BackupRun.objects.filter(status="COMPLETE").order_by("-created_at").first()
    if not latest or latest.created_at < timezone.now() - timedelta(
        hours=policy.backup_interval_hours
    ):
        destination = backup_directory() / (
            "scheduled-" + timezone.now().strftime("%Y%m%d%H%M%S%f") + ".btpv"
        )
        _, digest = create_backup(connection.settings_dict["NAME"], destination, backup_key())
        BackupRun.objects.create(filename=destination.name, sha256=digest)
        record(None, "backup.scheduled")
    # Keep at least the newest successful backup; missing/tampered files aren't safe recovery points.
    latest = BackupRun.objects.filter(status="COMPLETE").order_by("-created_at").first()
    newest_is_present = latest and (backup_directory() / Path(latest.filename).name).is_file()
    if not newest_is_present:
        return
    cutoff = timezone.now() - timedelta(days=policy.backup_retention_days)
    for backup in BackupRun.objects.filter(
        created_at__lt=cutoff, filename__startswith="scheduled-", status="COMPLETE"
    ).exclude(pk=latest.pk):
        target = (backup_directory() / Path(backup.filename).name).resolve()
        if target.parent != backup_directory():
            continue
        if target.is_file():
            target.unlink()
        backup.status = "EXPIRED"
        backup.save(update_fields=["status"])
        record(None, "backup.expired", obj=backup)


def run_cycle():
    from apps.verifactu.services import send_one

    if hold_path(connection.settings_dict["NAME"]).exists():
        heartbeat("operations_tasks", "HELD")
        return
    errors = []
    for label, task in [("FISCAL", send_one), ("BACKUP", run_backup_policy)]:
        try:
            result = task()
            if label == "FISCAL" and result in ("RETRY", "REJECTED", "ACCEPTED_WITH_ERRORS"):
                errors.append("FISCAL:" + result)
        except Exception as error:
            code = label + ":" + type(error).__name__
            errors.append(code)
            record(None, "operations.task_failed", outcome="FAILED", metadata={"error_code": code})
    heartbeat("operations_tasks", "DEGRADED" if errors else "RUNNING", ",".join(errors))
