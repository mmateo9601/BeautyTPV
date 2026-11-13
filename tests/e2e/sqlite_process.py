"""Isolated process driver used only by QA; never points at the installation DB."""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
if os.environ.get("BEAUTYTPV_TEST_PROCESS") != "1" or not os.environ.get("BEAUTYTPV_DB"):
    raise RuntimeError("QA requires an explicit isolated database and BEAUTYTPV_TEST_PROCESS=1")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connections  # noqa: E402

from apps.accounts.models import User  # noqa: E402
from apps.cash.models import CashRegister, CashSession  # noqa: E402
from apps.cash.services import open_session  # noqa: E402
from apps.catalog.models import CatalogItem  # noqa: E402
from apps.core.models import CompanySettings  # noqa: E402
from apps.hardware.models import Printer, PrintJob  # noqa: E402
from apps.layout.models import Section, Station  # noqa: E402
from apps.pos.models import OpenTicket, Sale  # noqa: E402
from apps.pos.services import add_line, checkout, open_ticket, prepare_payment  # noqa: E402
from apps.verifactu.models import FiscalRecord  # noqa: E402
from apps.verifactu.services import send_one, verify_chain  # noqa: E402

settings.FISCAL_PRODUCER = {"name": "Productor QA", "tax_id": "89890001K"}


def execute(command):
    action = command["action"]
    if action == "seed":
        call_command("migrate", verbosity=0, interactive=False)
        employee = User.objects.create_user(username="browser", role="MANAGER")
        employee.set_pin("827364")
        employee.save()
        employee.set_password("Browser-Password-194!")
        employee.save()
        User.objects.create_user(
            username="browser-admin", role="ADMIN", password="Browser-Admin-Password-194!"
        )
        company = CompanySettings.load()
        company.name = "Centro navegador QA"
        company.tax_id = "89890001K"
        company.address = "Pruebas 1"
        company.save()
        section = Section.objects.create(name="A")
        for index in range(1, 4):
            Station.objects.create(section=section, code=f"A{index}", name=f"Puesto A{index}")
        section_b = Section.objects.create(name="B")
        Station.objects.create(section=section_b, code="B1", name="Puesto B1")
        CatalogItem.objects.create(name="Manicura QA", price="12.10", tax_rate="21")
        register = CashRegister.objects.create(name="Principal QA")
        if command.get("open_cash", True):
            open_session(register, employee, "50.00")
        Printer.objects.create(name="Simulador QA", connection_type="SIMULATOR")
        return {"seeded": True}
    if action == "open":
        actor = User.objects.get(username="browser")
        ticket = open_ticket(Station.objects.get(code=command["station"]), actor)
        if command.get("add", False):
            add_line(ticket, CatalogItem.objects.get(name="Manicura QA"), actor)
        return {"ticket": ticket.pk, "total": str(OpenTicket.objects.get(pk=ticket.pk).total)}
    if action == "checkout":
        gate = command.get("gate")
        if gate:
            deadline = time.monotonic() + 20
            while not Path(gate).exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError("QA process barrier timed out")
                time.sleep(0.02)
        actor = User.objects.get(username="browser")
        ticket = OpenTicket.objects.get(pk=command["ticket"])
        if command.get("crash_before_commit"):
            from apps.hardware import services as hardware

            original = hardware.enqueue_invoice

            def crash(*args, **kwargs):
                original(*args, **kwargs)
                os._exit(91)  # Real process death with an uncommitted financial transaction.

            hardware.enqueue_invoice = crash
        sale = checkout(
            ticket,
            actor,
            [{"method": "CARD", "amount": "12.10", "reference": "CONFIRMED-EXTERNAL"}],
            command["key"],
        )
        return {"sale": sale.pk, "invoice": sale.invoice.full_number}
    if action == "prepare":
        ticket = prepare_payment(
            OpenTicket.objects.get(pk=command["ticket"]), User.objects.get(username="browser")
        )
        return {"status": ticket.status, "ticket": ticket.pk}
    if action == "inspect":
        tickets = {
            (ticket.station.code if ticket.station else f"QUICK-{ticket.pk}"): {
                "id": ticket.pk,
                "status": ticket.status,
                "total": str(ticket.total),
                "lines": ticket.lines.count(),
            }
            for ticket in OpenTicket.objects.select_related("station")
        }
        return {
            "tickets": tickets,
            "sales": Sale.objects.count(),
            "invoices": list(Sale.objects.values_list("invoice__series", "invoice__number")),
            "records": FiscalRecord.objects.count(),
            "print_jobs": PrintJob.objects.count(),
            "copies": PrintJob.objects.filter(kind="COPY").count(),
            "cash": [
                {
                    "expected": str(session.expected_balance),
                    "closed": bool(session.closed_at),
                    "difference": str(session.difference),
                }
                for session in CashSession.objects.order_by("pk")
            ],
            "chain_valid": verify_chain(),
        }
    if action == "send_one":
        return {"result": send_one()}
    raise ValueError("Unknown QA action")


if __name__ == "__main__":
    try:
        result = execute(json.loads(sys.argv[1]))
        print(json.dumps({"ok": True, **result}))
    except Exception as exc:
        print(json.dumps({"ok": False, "type": type(exc).__name__, "error": str(exc)}))
        sys.exit(2)
    finally:
        connections.close_all()
