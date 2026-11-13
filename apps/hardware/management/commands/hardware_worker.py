import time

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from apps.hardware.models import PrintJob
from apps.hardware.services import process_job, recover_expired


class Command(BaseCommand):
    help = "Bridge local ESC/POS. Ejecutar con cuenta OS autorizada en el servidor de dispositivos."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=float, default=2)

    def handle(self, *args, **options):
        from django.conf import settings

        from apps.support.operations import service_lock

        with service_lock(settings.DATABASES["default"]["NAME"]):
            return self.run_locked(*args, **options)

    def run_locked(self, *args, **options):
        while True:
            try:
                recover_expired()
            except ValidationError:
                if options["once"]:
                    self.stdout.write(
                        "Impresion retenida: concilie la restauracion antes de reanudar."
                    )
                    return
                time.sleep(max(options["interval"], 0.1))
                continue
            ids = list(
                PrintJob.objects.filter(
                    status="PENDING", printer__enabled=True, printer__terminal__isnull=True
                ).values_list("pk", flat=True)[:50]
            )
            for pk in ids:
                process_job(pk)
            if options["once"]:
                return
            time.sleep(max(options["interval"], 0.1))
