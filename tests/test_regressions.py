from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.billing.models import InvoiceLine
from apps.billing.services import rectify_invoice
from apps.cash.models import CashMovement, CashRegister
from apps.cash.services import add_movement, close_session, open_session
from apps.catalog.models import CatalogItem
from apps.hardware.services import enqueue_invoice, process_job
from apps.layout.models import Section, Station
from apps.pos.models import Payment
from apps.pos.services import add_line, checkout, open_ticket


@pytest.fixture
def closed_sale(db):
    employee = User.objects.create_user(username="reg-employee")
    manager = User.objects.create_user(username="reg-manager", role="MANAGER")
    session = open_session(CashRegister.objects.create(name="Regression"), employee, "50.00")
    station = Station.objects.create(section=Section.objects.create(name="R"), code="R1", name="R1")
    item = CatalogItem.objects.create(name="Servicio", price="12.10", tax_rate="21")
    ticket = open_ticket(station, employee)
    add_line(ticket, item, employee)
    sale = checkout(ticket, employee, [{"method": "CASH", "amount": "12.10"}], "reg-key", session)
    return employee, manager, session, sale


def test_stale_cash_session_cannot_refund_after_closure(closed_sale):
    employee, manager, session, sale = closed_sale
    close_session(session, manager, "62.10")
    assert session.closed_at is None  # Caller still holds a stale object.
    with pytest.raises(ValidationError):
        rectify_invoice(sale.invoice, manager, "Devolucion", "CASH", session)
    assert not sale.invoice.rectifications.exists()


def test_sealed_documents_reject_new_lines_and_payments(closed_sale):
    employee, manager, session, sale = closed_sale
    line = sale.invoice.lines.get()
    values = {
        field: getattr(line, field)
        for field in (
            "description",
            "quantity",
            "unit_price",
            "discount_percent",
            "tax_rate",
            "net_total",
            "tax_total",
            "total",
        )
    }
    with pytest.raises(IntegrityError), transaction.atomic():
        InvoiceLine.objects.create(invoice=sale.invoice, **values)
    with pytest.raises(IntegrityError), transaction.atomic():
        Payment.objects.create(sale=sale, method="CASH", amount="1", cash_session=session)
    assert sale.invoice.lines.count() == 1
    assert sale.payments.count() == 1


def test_restore_hold_blocks_services_and_physical_delivery(closed_sale, settings, tmp_path):
    employee, manager, session, sale = closed_sale
    settings.DATABASES = {
        "default": {**settings.DATABASES["default"], "NAME": str(tmp_path / "restored.sqlite3")}
    }
    (tmp_path / "restored.sqlite3.fiscal-restore-hold").write_text("reconcile")
    with pytest.raises(ValidationError):
        process_job(sale.invoice.print_jobs.get().pk)
    with pytest.raises(ValidationError):
        rectify_invoice(sale.invoice, manager, "Devolucion", reference="confirmed")
    with pytest.raises(ValidationError):
        enqueue_invoice(sale.invoice, employee, copy=True)


def test_copies_are_scoped_and_cash_movements_are_append_only(closed_sale):
    employee, manager, session, sale = closed_sale
    other = User.objects.create_user(username="reg-other")
    with pytest.raises(PermissionDenied):
        enqueue_invoice(sale.invoice, other, copy=True)
    movement = add_movement(session, manager, "IN", Decimal("1.00"), "Fondo")
    with pytest.raises(IntegrityError), transaction.atomic():
        CashMovement.objects.bulk_create(
            [
                CashMovement(
                    id=movement.pk,
                    session=session,
                    kind="IN",
                    amount="999",
                    reason="Fondo",
                    actor=manager,
                )
            ],
            update_conflicts=True,
            update_fields=["amount"],
            unique_fields=["id"],
        )
    movement.refresh_from_db()
    assert movement.amount == Decimal("1.00")


def test_superadmin_panel_renders_real_queue_actions(closed_sale, client):
    from django.utils import timezone

    user = User.objects.create_user(username="panel-tech", role="SUPERADMIN")
    client.force_login(user)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    response = client.get("/soporte/")
    assert response.status_code == 200
    assert b"printer_id" in response.content
    assert b"/recuperar/" in response.content


def test_release_package_contains_versioned_schemas_without_runtime_data(tmp_path):
    import zipfile

    from apps.support.updates import validate_package
    from scripts.package_release import build_package

    root = tmp_path / "source"
    (root / "schemas").mkdir(parents=True)
    (root / "schemas" / "sample.xsd").write_text("schema")
    (root / "README.md").write_text("Installation")
    (root / ".env").write_text("SECRET=not-to-package")
    (root / "db.sqlite3").write_bytes(b"private")
    output = tmp_path / "release.zip"
    digest = build_package(root, output, "0.1.0")
    manifest = validate_package(output, digest)
    assert manifest["version"] == "0.1.0"
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {"README.md", "schemas/sample.xsd", "release.json"}


def test_category_management_is_usable_and_protects_assigned_items(db, client):
    from apps.catalog.models import Category

    employee = User.objects.create_user(username="category-employee")
    client.force_login(employee)
    assert client.post("/catalogo/categorias/", {"name": "Cabina"}).status_code == 403
    admin = User.objects.create_user(username="category-admin", role="ADMIN")
    client.force_login(admin)
    assert client.get("/catalogo/categorias/").status_code == 200
    assert client.post("/catalogo/categorias/", {"name": "Cabina"}).status_code == 302
    category = Category.objects.get(name="Cabina")
    assert (
        client.post(f"/catalogo/categorias/{category.pk}/", {"name": "Servicios"}).status_code
        == 302
    )
    item = CatalogItem.objects.create(
        name="Tratamiento", category=category, price="10", tax_rate="10"
    )
    assert client.post(f"/catalogo/categorias/{category.pk}/eliminar/").status_code == 400
    item.category = None
    item.save()
    assert client.post(f"/catalogo/categorias/{category.pk}/eliminar/").status_code == 302


def test_customer_export_and_unused_deletion_require_elevated_admin(db, client):
    from django.utils import timezone

    from apps.customers.models import Customer

    employee = User.objects.create_user(username="customer-employee")
    admin = User.objects.create_user(username="customer-admin", role="ADMIN")
    customer = Customer.objects.create(name="=SUM(1,2)", phone="+34123456789")
    client.force_login(employee)
    assert client.get("/clientes/?format=csv").status_code == 403
    assert client.post(f"/clientes/{customer.pk}/eliminar/").status_code == 403
    client.force_login(admin)
    assert client.get("/clientes/?format=csv").status_code == 403
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    response = client.get("/clientes/?format=csv")
    assert response.status_code == 200
    assert b"'=SUM" in response.content
    assert b"'+34" in response.content
    assert client.post(f"/clientes/{customer.pk}/eliminar/").status_code == 302
    protected = Customer.objects.create(name="Con cuenta")
    from apps.pos.models import OpenTicket

    OpenTicket.objects.create(customer=protected, created_by=employee)
    assert client.post(f"/clientes/{protected.pk}/eliminar/").status_code == 400
    assert Customer.objects.filter(pk=protected.pk).exists()
