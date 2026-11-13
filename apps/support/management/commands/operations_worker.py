import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.support.operations import service_lock
from apps.support.scheduler import run_cycle


class Command(BaseCommand):
    help = "Worker local: remisión diferida y política de backup aisladas ante fallos"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=float, default=10)

    def handle(self, *args, **options):
        with service_lock(settings.DATABASES["default"]["NAME"]):
            while True:
                close_old_connections()
                run_cycle()
                if options["once"]:
                    return
                time.sleep(max(1, options["interval"]))
