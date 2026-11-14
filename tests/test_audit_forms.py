"""Positive rendered-form -> HTTP POST -> database checks beyond the denial matrix."""

from decimal import Decimal

from django.test import Client
from django.urls import reverse
from test_audit_matrix import audit_centre, signed_client  # noqa: F401

from apps.accounts.models import User
from apps.billing.models import Refund
from apps.catalog.models import CatalogItem
from apps.core.models import CompanySettings
from apps.customers.models import Customer
from apps.hardware.models import PrintJob
from apps.pos.models import OpenTicket


def test_admin_company_configuration_form_persists_validated_values(audit_centre):  # noqa: F811
    client = signed_client(audit_centre, "ADMIN")
    assert client.get("/empresa/").status_code == 200
    payload = {
        "name": "Empresa editada",
        "tax_id": "89890001K",
        "address": "Calle sintetica",
        "timezone": "Atlantic/Canary",
        "producer_name": "Productor sintetico",
        "producer_tax_id": "89890001K",
        # A fiscal fixture already exists: the installation identity is now
        # deliberately fixed. Independent negative cases prove the new guard.
        "installation_number": CompanySettings.load().installation_number,
        "quick_sale_enabled": "on",
        "simplified_series": "S2",
        "full_series": "F2",
        "rectification_series": "R2",
    }
    assert client.post("/empresa/", payload).status_code == 302
    company = CompanySettings.load()
    assert company.name == payload["name"] and company.timezone == payload["timezone"]
    assert company.quick_sale_enabled and company.full_series == "F2"


def test_customer_and_catalog_forms_save_and_preserve_history(audit_centre):  # noqa: F811
    employee = signed_client(audit_centre, "EMPLOYEE")
    customer_data = {
        "name": "Ficha HTTP",
        "phone": "600000000",
        "email": "audit@example.test",
        "tax_id": "",
        "address": "",
        "legal_basis": "Ejecucion de contrato",
    }
    assert employee.get(reverse("customers:create")).status_code == 200
    assert employee.post(reverse("customers:create"), customer_data).status_code == 302
    customer = Customer.objects.get(name="Ficha HTTP")
    customer_data["phone"] = "600000001"
    assert (
        employee.post(reverse("customers:edit", args=[customer.pk]), customer_data).status_code
        == 302
    )
    customer.refresh_from_db()
    assert customer.phone == "600000001"
    admin = signed_client(audit_centre, "ADMIN")
    payload = {
        "name": "Articulo HTTP",
        "kind": "PRODUCT",
        "price": "11.00",
        "tax_rate": "10",
        "category": audit_centre["category"].pk,
        "active": "on",
    }
    assert admin.post(reverse("catalog:create"), payload).status_code == 302
    item = CatalogItem.objects.get(name="Articulo HTTP")
    payload["price"] = "22.00"
    payload.pop("active")
    assert admin.post(reverse("catalog:edit", args=[item.pk]), payload).status_code == 302
    item.refresh_from_db()
    assert item.price == Decimal("22.00") and not item.active
    assert audit_centre["invoice"].total == Decimal("12.10")


def test_manager_line_discount_cancellation_movements_and_cash_close(audit_centre):  # noqa: F811
    client = signed_client(audit_centre, "MANAGER")
    line, ticket, session = (audit_centre[key] for key in ("line", "ticket", "cash_session"))
    ticket.refresh_from_db()
    assert (
        client.post(
            reverse("pos:update_line", args=[line.pk]),
            {
                "quantity": "2",
                "discount_percent": "10",
                "note": "Cambio HTTP",
                "version": ticket.version,
            },
        ).status_code
        == 302
    )
    line.refresh_from_db()
    assert line.total == Decimal("21.78") and line.note == "Cambio HTTP"
    ticket.refresh_from_db()
    assert (
        client.post(
            reverse("pos:cancel_ticket", args=[ticket.pk]), {"version": ticket.version}
        ).status_code
        == 302
    )
    assert OpenTicket.objects.get(pk=ticket.pk).cancelled_by == audit_centre["users"]["MANAGER"]
    assert (
        client.post(
            reverse("cash:movement", args=[session.pk]),
            {"kind": "IN", "amount": "5", "reason": "Fondo autorizado"},
        ).status_code
        == 302
    )
    assert (
        client.post(
            reverse("cash:movement", args=[session.pk]),
            {"kind": "OUT", "amount": "2", "reason": "Retirada autorizada"},
        ).status_code
        == 302
    )
    assert (
        client.post(reverse("cash:close", args=[session.pk]), {"counted": "53.00"}).status_code
        == 302
    )
    session.refresh_from_db()
    assert session.closed_at and session.difference == 0


def test_manager_cash_refund_from_invoice_form_reconciles_database(audit_centre):  # noqa: F811
    client = signed_client(audit_centre, "MANAGER")
    invoice, session = audit_centre["invoice"], audit_centre["cash_session"]
    assert client.get(reverse("billing:detail", args=[invoice.pk])).status_code == 200
    response = client.post(
        reverse("billing:rectify", args=[invoice.pk]),
        {
            "reason": "Devolucion total HTTP",
            "method": "CASH",
            "cash_session": session.pk,
            "reference": "SYNTHETIC-RETURN",
        },
    )
    assert response.status_code == 302
    refund = Refund.objects.get()
    assert refund.invoice.rectifies == invoice and refund.amount == Decimal("12.10")
    assert session.expected_balance == Decimal("37.90")
    invoice.refresh_from_db()
    assert invoice.total == Decimal("12.10")


def test_superadmin_queue_controls_create_real_jobs_and_corrections(audit_centre):  # noqa: F811
    client = signed_client(audit_centre, "SUPERADMIN")
    item, job, printer = (audit_centre[key] for key in ("outbox", "job", "printer"))
    type(item).objects.filter(pk=item.pk).update(status="RETRY")
    assert client.post(reverse("support:recover_fiscal", args=[item.pk])).status_code == 302
    item.refresh_from_db()
    assert item.status == "PENDING"
    PrintJob.objects.filter(pk=job.pk).update(status="FAILED")
    assert (
        client.post(
            reverse("hardware:retry", args=[job.pk]), {"printer_id": printer.pk}
        ).status_code
        == 302
    )
    assert PrintJob.objects.get(pk=job.pk).status == "PENDING"
    assert (
        client.post(reverse("hardware:test", args=[printer.pk]), {"drawer": "1"}).status_code == 302
    )
    assert PrintJob.objects.filter(kind="DRAWER", open_drawer=True).count() == 1
    type(item).objects.filter(pk=item.pk).update(status="REJECTED")
    original = item.record.xml
    assert client.post(reverse("support:correct_fiscal", args=[item.pk])).status_code == 302
    assert item.record.invoice.fiscal_records.count() == 2
    item.record.refresh_from_db()
    assert item.record.xml == original


def test_admin_user_creation_and_pin_change_revoke_logged_in_operator(audit_centre):  # noqa: F811
    admin = signed_client(audit_centre, "ADMIN")
    response = admin.post(
        reverse("team:index"),
        {
            "username": "new-http-operator",
            "first_name": "Operador prueba",
            "role": "EMPLOYEE",
            "pin": "739184",
            "password": "",
        },
    )
    assert response.status_code == 302
    operator = User.objects.get(username="new-http-operator")
    logged = Client()
    assert (
        logged.post("/acceso/", {"username": operator.username, "credential": "739184"}).status_code
        == 302
    )
    assert logged.get("/tpv/").status_code == 200
    assert (
        admin.post(
            reverse("team:edit", args=[operator.pk]),
            {"role": "EMPLOYEE", "active": "on", "pin": "840295", "password": ""},
        ).status_code
        == 302
    )
    assert logged.get("/tpv/").status_code == 403


def test_employee_cash_screen_hides_other_employees_closed_sessions(audit_centre):  # noqa: F811
    from apps.cash.models import CashRegister
    from apps.cash.services import close_session, open_session

    manager = audit_centre["users"]["MANAGER"]
    other = open_session(CashRegister.objects.create(name="Caja de supervision"), manager, "77")
    close_session(other, manager, "77")
    employee = signed_client(audit_centre, "EMPLOYEE")
    response = employee.get("/caja/")
    assert response.status_code == 200
    assert other not in response.context["sessions"]
    assert audit_centre["cash_session"] in response.context["sessions"]
    assert other in signed_client(audit_centre, "MANAGER").get("/caja/").context["sessions"]
