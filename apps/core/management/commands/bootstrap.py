from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cash.models import CashRegister
from apps.core.models import CompanySettings
from apps.layout.models import Section, Station


class Command(BaseCommand):
    help = "Inicializa empresa, plano A/B y caja; nunca crea usuarios ni credenciales."

    @transaction.atomic
    def handle(self, *args, **options):
        CompanySettings.load()
        for order, (name, count) in enumerate([("A", 3), ("B", 1)]):
            section, _ = Section.objects.get_or_create(name=name, defaults={"sort_order": order})
            for index in range(1, count + 1):
                code = f"{name}{index}"
                Station.objects.get_or_create(
                    code=code, defaults={"section": section, "name": code}
                )
        CashRegister.objects.get_or_create(name="Caja principal")
        self.stdout.write(
            self.style.SUCCESS("Instalación inicial creada sin credenciales predeterminadas.")
        )
