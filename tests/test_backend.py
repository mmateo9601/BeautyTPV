from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.accounts.models import User
from apps.cash.models import CashRegister
from apps.cash.services import add_movement, close_session, open_session
from apps.catalog.models import CatalogItem
from apps.core.models import CompanySettings
from apps.layout.models import Section, Station
from apps.pos.models import OpenTicket, Payment, Sale
from apps.pos.services import (
    TicketConflict,
    add_line,
    checkout,
    open_ticket,
    remove_line,
    update_line,
)


@pytest.fixture
def operation(db):
    employee = User.objects.create_user(username="employee", role="EMPLOYEE")
    manager = User.objects.create_user(username="manager", role="MANAGER")
    company = CompanySettings.load()
    company.name = "Beauty prueba"
    company.tax_id = "B12345674"
    company.address = "Calle prueba 1"
    company.save()
    section = Section.objects.create(name="A")
    station = Station.objects.create(section=section, code="A1", name="A1")
    item = CatalogItem.objects.create(name="Manicura", price="24.20", tax_rate="21")
    register = CashRegister.objects.create(name="Principal")
    session = open_session(register, employee, Decimal("50.00"))
    ticket = open_ticket(station, employee)
    return employee, manager, station, item, session, ticket


def test_bootstrap_is_idempotent_and_no_credentials(db):
    call_command("bootstrap")
    call_command("bootstrap")
    assert Station.objects.count() == 4
    assert User.objects.count() == 0
    assert CashRegister.objects.count() == 1


def test_two_accounts_and_snapshot_persist(operation):
    employee, manager, station, item, session, ticket = operation
    add_line(ticket, item, employee)
    other = Station.objects.create(section=station.section, code="A2", name="A2")
    second = open_ticket(other, employee)
    assert open_ticket(station, employee).pk == ticket.pk
    item.price = Decimal("99")
    item.save()
    ticket.refresh_from_db()
    assert ticket.total == Decimal("24.20")
    assert second.total == 0
    assert ticket.lines.get().net_total == Decimal("20.00")


def test_discount_and_version(operation):
    employee, manager, station, item, session, ticket = operation
    with pytest.raises(PermissionDenied):
        add_line(ticket, item, employee, discount_percent=10)
    line = add_line(ticket, item, manager, discount_percent=10, expected_version=0)
    assert line.total == Decimal("21.78")
    with pytest.raises(TicketConflict):
        add_line(ticket, item, employee, expected_version=0)
    with pytest.raises(PermissionDenied):
        remove_line(line, employee)
    with pytest.raises(ValidationError):
        update_line(line, manager, quantity=0)


def test_payment_mixed_idempotent_and_reconciliation(operation):
    employee, manager, station, item, session, ticket = operation
    add_line(ticket, item, employee)
    payments = [
        {"method": "CASH", "amount": Decimal("10.00"), "received": Decimal("20.00")},
        {"method": "CARD", "amount": Decimal("14.20"), "reference": "terminal-confirmed-1"},
    ]
    sale = checkout(ticket, employee, payments, "same-request", session)
    assert checkout(ticket, employee, payments, "same-request", session).pk == sale.pk
    assert Sale.objects.count() == 1
    assert Payment.objects.count() == 2
    assert sale.invoice.total == Decimal("24.20")
    assert session.expected_balance == Decimal("60.00")
    assert sale.payments.get(method="CASH").change == 10
    with pytest.raises(ValidationError):
        checkout(ticket, employee, payments, "second-request", session)
    with pytest.raises(ValidationError):
        checkout(ticket, employee, [{"method": "CASH", "amount": "24.20"}], "same-request", session)
    close_session(session, manager, "60.00")
    session.refresh_from_db()
    assert session.difference == 0


def test_invalid_checkout_rolls_back(operation):
    employee, manager, station, item, session, ticket = operation
    add_line(ticket, item, employee)
    for payments in [
        [{"method": "CASH", "amount": "24.19"}],
        [{"method": "CARD", "amount": "24.20"}],
        [{"method": "CASH", "amount": "24.20", "received": "20.00"}],
    ]:
        with pytest.raises(ValidationError):
            checkout(ticket, employee, payments, "bad", session)
    ticket.refresh_from_db()
    assert ticket.status == "OPEN"
    assert Sale.objects.count() == 0
    with pytest.raises(ValidationError):
        checkout(ticket, employee, [{"method": "CASH", "amount": "24.20"}], "no-session")


def test_cash_permissions_and_constraints(operation):
    employee, manager, station, item, session, ticket = operation
    with pytest.raises(PermissionDenied):
        close_session(session, employee, "50")
    with pytest.raises(PermissionDenied):
        add_movement(session, employee, "OUT", "1", "test")
    add_movement(session, manager, "IN", "10", "Fondo adicional")
    add_movement(session, manager, "OUT", "5", "Retirada")
    assert session.expected_balance == 55
    with pytest.raises(ValidationError):
        open_session(session.register, employee, "0")
    close_session(session, manager, "54")
    session.refresh_from_db()
    assert session.difference == -1
    with pytest.raises(ValidationError):
        add_movement(session, manager, "IN", "1", "cerrada")


def test_unique_ticket_and_issued_immutability(operation):
    employee, manager, station, item, session, ticket = operation
    with pytest.raises(IntegrityError), transaction.atomic():
        OpenTicket.objects.create(station=station, created_by=employee)
    add_line(ticket, item, employee)
    sale = checkout(
        ticket,
        employee,
        [{"method": "CARD", "amount": "24.20", "reference": "confirmed"}],
        "immutable",
    )
    with pytest.raises(ValidationError):
        sale.delete()
    with pytest.raises(ValidationError):
        Sale.objects.filter(pk=sale.pk).update(total=0)
    with pytest.raises(ValidationError):
        add_line(ticket, item, employee)
    with pytest.raises(ProtectedError):
        station.delete()
