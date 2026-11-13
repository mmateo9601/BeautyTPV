import time
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from apps.audit.services import record
from apps.support.models import BackupRun, TechnicalSettings
from apps.support.operations import backup_directory, backup_key, create_backup, hold_path
from apps.verifactu.services import send_one


class Command(BaseCommand):
    help = "Worker local: remisión fiscal diferida y política de backup cifrado"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=float, default=10)

    def handle(self, *args, **options):
        from django.conf import settings

        from apps.support.operations import service_lock

        with service_lock(settings.DATABASES["default"]["NAME"]):
            return self.run_locked(*args, **options)

    def run_locked(self, *args, **options):
        while True:
            database = connection.settings_dict["NAME"]
            if not hold_path(database).exists():
                send_one()
                policy = TechnicalSettings.load()
                latest = BackupRun.objects.filter(status="COMPLETE").order_by("-created_at").first()
                if not latest or latest.created_at < timezone.now() - timedelta(
                    hours=policy.backup_interval_hours
                ):
                    try:
                        destination = backup_directory() / (
                            "scheduled-" + timezone.now().strftime("%Y%m%d%H%M%S%f") + ".btpv"
                        )
                        _, digest = create_backup(database, destination, backup_key())
                        BackupRun.objects.create(filename=destination.name, sha256=digest)
                        record(None, "backup.scheduled")
                    except (ValueError, OSError):
                        record(None, "backup.failed", outcome="FAILED")
                cutoff = timezone.now() - timedelta(days=policy.backup_retention_days)
                # Policy applies only registered scheduled backups; manual/pre-update copies retained.
                for backup in BackupRun.objects.filter(
                    created_at__lt=cutoff, filename__startswith="scheduled-", status="COMPLETE"
                ):
                    target = (backup_directory() / Path(backup.filename).name).resolve()
                    if target.parent == backup_directory() and target.is_file():
                        target.unlink()
                    backup.status = "EXPIRED"
                    backup.save(update_fields=["status"])
            if options["once"]:
                return
            time.sleep(max(1, options["interval"]))
