from django.core.management.base import BaseCommand

from apps.verifactu.services import send_one


class Command(BaseCommand):
    help = "Remite registros pendientes a AEAT con certificado cliente configurado."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        from django.conf import settings

        from apps.support.operations import service_lock

        with service_lock(settings.DATABASES["default"]["NAME"]):
            return self.run_locked(*args, **options)

    def run_locked(self, *args, **options):
        for _ in range(options["limit"]):
            status = send_one()
            if status is None:
                break
            self.stdout.write(status)
