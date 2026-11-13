"""Behavioural audit additions: state transitions, inputs, reporting and persistence."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.urls import reverse
from django.utils import timezone
from test_backend import operation  # noqa: F401

from apps.accounts.models import User
from apps.cash.services import add_movement, close_session
from apps.catalog.models import CatalogItem, Category
from apps.core.models import CompanySettings, Terminal
from apps.core.transactions import atomic_retry
from apps.hardware.models import Printer
from apps.layout.models import Section, Station
from apps.pos.models import OpenTicket, Sale
from apps.pos.services import (
    add_line,
    cancel_ticket,
    checkout,
    open_ticket,
    prepare_payment,
    quick_ticket,
    resume_ticket,
    update_line,
)


def elevate(client, user):
    client.force_login(user)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()


def test_payment_pending_persists_blocks_edits_and_can_checkout(operation):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    line = add_line(ticket, item, employee, note="Nota persistente")
    ticket.refresh_from_db()
    pending = prepare_payment(ticket, employee, ticket.version)
    assert OpenTicket.objects.get(pk=ticket.pk).status == "PAYMENT_PENDING"
    with pytest.raises(ValidationError):
        update_line(line, employee, note="No permitido")
    sale = checkout(
        pending, employee, [{"method": "CASH", "amount": "24.20"}], "pending-checkout", session
    )
    assert sale.invoice.total == Decimal("24.20")
    ticket.refresh_from_db()
    assert ticket.status == "CLOSED"
    assert ticket.lines.get().note == "Nota persistente"


def test_prepare_empty_and_conflicting_resume_do_not_lose_account(operation):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    with pytest.raises(ValidationError):
        prepare_payment(ticket, employee)
    add_line(ticket, item, employee)
    pending = prepare_payment(ticket, employee)
    with pytest.raises(ValidationError):
        resume_ticket(pending, employee, pending.version - 1)
    resumed = resume_ticket(pending, employee, pending.version)
    assert resumed.status == "OPEN" and resumed.lines.count() == 1


def test_quick_sale_requires_configuration_and_is_reused_per_terminal(operation, client):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    with pytest.raises(ValidationError):
        quick_ticket(employee)
    company = CompanySettings.load()
    company.quick_sale_enabled = True
    company.save()
    first = Terminal.objects.create(code="first", name="Primero")
    second = Terminal.objects.create(code="second", name="Segundo")
    account = quick_ticket(employee, first)
    assert quick_ticket(employee, first).pk == account.pk
    assert quick_ticket(employee, second).pk != account.pk
    client.force_login(employee)
    assert client.post(reverse("pos:quick_sale")).status_code == 302
    assert b"Venta" in client.get("/tpv/").content


def test_notes_and_category_filter_are_real_http_to_database(operation, client):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    category = Category.objects.create(name="Auditoria")
    item.category = category
    item.save()
    other = CatalogItem.objects.create(name="No pertenece", price="1", tax_rate="10")
    client.force_login(employee)
    response = client.get(reverse("pos:ticket", args=[ticket.pk]), {"category": category.pk})
    assert list(response.context["items"]) == [item]
    response = client.post(
        reverse("pos:add_line", args=[ticket.pk]),
        {"item_id": item.pk, "note": "Preferencia", "version": ticket.version},
    )
    assert response.status_code == 302
    line = ticket.lines.get()
    assert line.note == "Preferencia"
    response = client.post(reverse("pos:update_line", args=[line.pk]), {"note": "n" * 501})
    assert response.status_code == 400
    line.refresh_from_db()
    assert line.note == "Preferencia"
    assert other.active


@pytest.mark.parametrize("bad", ["text", "-1", "9" * 20, "NaN"])
def test_post_foreign_keys_are_validated_without_500(operation, client, bad):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    client.force_login(employee)
    assert (
        client.post(reverse("pos:add_line", args=[ticket.pk]), {"item_id": bad}).status_code == 400
    )
    assert (
        client.post(reverse("pos:customer", args=[ticket.pk]), {"customer_id": bad}).status_code
        == 400
    )
    assert client.post(reverse("cash:open"), {"register_id": bad}).status_code == 400
    assert (
        client.post(reverse("pos:checkout", args=[ticket.pk]), {"cash_session_id": bad}).status_code
        == 400
    )


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "1e1000000", "10000000000.00"])
def test_extreme_money_never_creates_partial_sale(operation, bad):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    add_line(ticket, item, employee)
    with pytest.raises(ValidationError):
        checkout(ticket, employee, [{"method": "CASH", "amount": bad}], "invalid-money", session)
    assert not Sale.objects.exists()
    assert OpenTicket.objects.get(pk=ticket.pk).status == "OPEN"


def test_checkout_routes_receipt_and_drawer_to_paying_terminal(operation):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    first = Terminal.objects.create(code="origin", name="Origen")
    paying = Terminal.objects.create(code="paying", name="Cobro")
    OpenTicket.objects.filter(pk=ticket.pk).update(terminal=first)
    printer = Printer.objects.create(
        name="Impresora del cobro", terminal=paying, connection_type="SIMULATOR"
    )
    add_line(ticket, item, employee)
    sale = checkout(
        ticket,
        employee,
        [{"method": "CASH", "amount": "24.20"}],
        "terminal-pay",
        session,
        terminal=paying,
    )
    job = sale.invoice.print_jobs.get()
    assert job.printer == printer and job.open_drawer
    assert sale.ticket.terminal == paying


def test_all_critical_services_obey_maintenance(operation):  # noqa: F811
    from apps.support.models import TechnicalSettings

    employee, manager, station, item, session, ticket = operation
    policy = TechnicalSettings.load()
    policy.maintenance = True
    policy.save()
    for call in [
        lambda: add_line(ticket, item, employee),
        lambda: open_ticket(station, employee),
        lambda: cancel_ticket(ticket, manager),
        lambda: close_session(session, manager, "50"),
        lambda: add_movement(session, manager, "IN", "1", "Motivo"),
    ]:
        with pytest.raises(ValidationError):
            call()
    assert ticket.lines.count() == 0


def test_sqlite_retry_rolls_back_whole_unit_before_repeat(db):
    attempts = []

    @atomic_retry
    def write_once():
        Category.objects.create(name="Una sola vez")
        attempts.append(True)
        if len(attempts) == 1:
            raise OperationalError("database is locked")

    # Simulate a top-level call while pytest keeps its outer rollback transaction.
    # The assertion is about savepoint rollback; real OS writers remain covered by E05/E13.
    with (
        patch("apps.core.transactions.connection.in_atomic_block", False),
        patch("apps.core.transactions.time.sleep"),
    ):
        write_once()
    assert Category.objects.filter(name="Una sola vez").count() == 1
    assert len(attempts) == 2


def test_reports_filters_cancellation_and_tax_snapshot(operation, client):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    add_line(ticket, item, employee)
    sale = checkout(
        ticket,
        employee,
        [
            {"method": "CASH", "amount": "12.10"},
            {"method": "CARD", "amount": "12.10", "reference": "AUDIT"},
        ],
        "reporting",
        session,
    )
    unused = Station.objects.create(section=station.section, code="CANCEL", name="Anulacion")
    cancelled = open_ticket(unused, employee)
    add_line(cancelled, item, employee)
    cancel_ticket(cancelled, manager)
    client.force_login(manager)
    response = client.get(
        "/informes/", {"employee_id": employee.pk, "register_id": session.register_id}
    )
    assert response.status_code == 200
    assert response.context["totals"]["total"] == sale.total
    assert sum(row["total"] for row in response.context["payments"]) == sale.total
    assert response.context["tax_totals"][0]["net_total"] == Decimal("20.00")
    unfiltered = client.get("/informes/")
    assert unfiltered.context["cancellations"].get().pk == cancelled.pk
    assert unfiltered.context["invoices"].count() == 1
    assert client.get("/informes/", {"end": "9999-12-31"}).status_code == 400
    assert client.get("/informes/", {"method": "UNKNOWN"}).status_code == 400
    assert client.get("/informes/", {"format": "csv"})["Content-Type"].startswith("text/csv")


def test_replacement_cannot_rewrite_sale_or_closed_ticket(operation):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    add_line(ticket, item, employee)
    sale = checkout(
        ticket, employee, [{"method": "CARD", "amount": "24.20", "reference": "OK"}], "sealed"
    )
    from django.db import connection

    with pytest.raises(IntegrityError), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO pos_sale (id,ticket_id,total,created_by_id,created_at,idempotency_key,request_fingerprint) SELECT id,ticket_id,99,created_by_id,created_at,idempotency_key,request_fingerprint FROM pos_sale WHERE id=%s",
                [sale.pk],
            )
    with pytest.raises(IntegrityError), transaction.atomic():
        OpenTicket.objects.filter(pk=ticket.pk).update(status="OPEN")


def test_sections_and_company_settings_validate_real_admin_changes(operation, client):  # noqa: F811
    employee, manager, station, item, session, ticket = operation
    admin = User.objects.create_user(username="audit-settings", role="ADMIN")
    elevate(client, admin)
    response = client.post(
        reverse("layout:section_edit", args=[station.section_id]),
        {"name": "Renombrada", "sort_order": "2"},
    )
    assert response.status_code == 302
    assert (
        client.post(reverse("layout:section_delete", args=[station.section_id])).status_code == 400
    )
    empty = Section.objects.create(name="Sin puestos")
    assert client.post(reverse("layout:section_delete", args=[empty.pk])).status_code == 302
    company = CompanySettings.load()
    company.timezone = "No/Such_Zone"
    with pytest.raises(ValidationError):
        company.full_clean()
    company.timezone = "Europe/Madrid"
    company.full_series = company.simplified_series
    with pytest.raises(ValidationError):
        company.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        CompanySettings.objects.bulk_create([CompanySettings(pk=2)])


def test_sum_of_valid_payment_components_cannot_overflow_sale_field(operation):  # noqa: F811
    from apps.customers.models import Customer
    from apps.pos.services import set_customer

    employee, manager, station, item, session, ticket = operation
    customer = Customer.objects.create(
        name="Cliente sintetico", tax_id="89890001K", address="Pruebas"
    )
    set_customer(ticket, customer, employee)
    item.price = Decimal("6000000000")
    item.save()
    add_line(ticket, item, employee, quantity=Decimal("2"))
    with pytest.raises(ValidationError):
        checkout(
            ticket,
            employee,
            [
                {"method": "CARD", "amount": "6000000000", "reference": "SYNTHETIC-A"},
                {"method": "CARD", "amount": "6000000000", "reference": "SYNTHETIC-B"},
            ],
            "overflowing-total",
        )
    assert not Sale.objects.exists()
