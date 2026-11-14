"""Positive business configuration and negative service authorization; real SQLite."""

import io

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from test_audit_matrix import audit_centre as audit_centre

from apps.cash.models import CashRegister
from apps.cash.services import open_session, save_register
from apps.catalog.models import Category
from apps.catalog.services import save_catalog_item, save_category
from apps.core.models import CompanySettings, Terminal
from apps.core.services import save_company_settings
from apps.layout.models import Section
from apps.layout.services import save_section, save_station
from apps.pos.services import add_line

pytestmark = pytest.mark.django_db


def admin_client(centre):
    client = Client()
    client.force_login(centre["users"]["ADMIN"])
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    return client


def test_commercial_settings_partial_save_preserves_fiscal_identity(audit_centre):
    admin = audit_centre["users"]["ADMIN"]
    original = CompanySettings.load()
    company = save_company_settings(
        admin, {"trade_name": "Salón de prueba", "email": "centro@example.test", "theme": "ocean"}
    )
    assert company.trade_name == "Salón de prueba"
    assert company.email == "centro@example.test" and company.theme == "ocean"
    assert company.tax_id == original.tax_id and company.name == original.name


@pytest.mark.parametrize(
    "data",
    [
        {"currency": "USD"},
        {"theme": "<style>"},
        {"timezone": "Invalid/Zone"},
        {"email": "no-mail"},
        {"fiscal_mode": "PRODUCTION"},
    ],
)
def test_invalid_company_settings_rejected_without_mutation(audit_centre, data):
    previous = CompanySettings.load().theme
    with pytest.raises(ValidationError):
        save_company_settings(audit_centre["users"]["ADMIN"], data)
    assert CompanySettings.load().theme == previous


@pytest.mark.parametrize("field", ["tax_id", "installation_number"])
def test_company_identity_cannot_be_reassigned_after_invoice(audit_centre, field):
    before = getattr(CompanySettings.load(), field)
    with pytest.raises(ValidationError, match="instalación"):
        save_company_settings(audit_centre["users"]["ADMIN"], {field: "DIFFERENT"})
    assert getattr(CompanySettings.load(), field) == before


def test_logo_canonical_and_served_only_to_authenticated_user(audit_centre):
    target = io.BytesIO()
    Image.new("RGB", (1000, 200), "#48706b").save(target, "JPEG")
    image = SimpleUploadedFile("untrusted.html", target.getvalue(), content_type="text/html")
    company = save_company_settings(audit_centre["users"]["ADMIN"], {}, logo=image)
    assert bytes(company.logo_data).startswith(b"\x89PNG")
    logo = Image.open(io.BytesIO(company.logo_data))
    assert logo.size == (600, 120)
    public = Client().get(reverse("core:logo"))
    assert public.status_code == 403
    employee = Client()
    employee.force_login(audit_centre["users"]["EMPLOYEE"])
    response = employee.get(reverse("core:logo"))
    assert response.status_code == 200 and response["Content-Type"] == "image/png"
    assert response["X-Content-Type-Options"] == "nosniff"
    save_company_settings(audit_centre["users"]["ADMIN"], {}, remove_logo=True)
    assert employee.get(reverse("core:logo")).status_code == 404


def test_commercial_settings_http_and_invalid_section(audit_centre):
    client = admin_client(audit_centre)
    response = client.post(
        reverse("core:settings") + "?section=commercial",
        {
            "trade_name": "Salón HTTP",
            "phone": "+34910000000",
            "email": "http@example.test",
            "commercial_address": "Pruebas 2",
            "ticket_footer": "Gracias",
        },
    )
    assert response.status_code == 302
    assert CompanySettings.load().trade_name == "Salón HTTP"
    assert client.get(reverse("core:settings") + "?section=bad").status_code == 400


def test_category_hiding_blocks_new_line_and_preserves_existing(audit_centre):
    admin = audit_centre["users"]["ADMIN"]
    item = audit_centre["item"]
    ticket = audit_centre["ticket"]
    line = add_line(ticket, item, audit_centre["users"]["EMPLOYEE"])
    category = item.category
    category.visible_in_pos = False
    save_category(admin, category)
    with pytest.raises(ValidationError, match="disponible"):
        add_line(ticket, item, audit_centre["users"]["EMPLOYEE"])
    assert ticket.lines.filter(pk=line.pk).exists()
    item.sort_order = 9
    save_catalog_item(admin, item)
    assert item.sort_order == 9


def test_station_open_account_blocks_disable_and_reassign(audit_centre):
    station = audit_centre["ticket"].station
    station.active = False
    with pytest.raises(ValidationError, match="abierta"):
        save_station(audit_centre["users"]["ADMIN"], station)
    station.refresh_from_db()
    station.section = Section.objects.create(name="Destino")
    with pytest.raises(ValidationError, match="abierta"):
        save_station(audit_centre["users"]["ADMIN"], station)


def test_register_crud_open_session_guard_and_stale_disabled(audit_centre):
    admin = audit_centre["users"]["ADMIN"]
    employee = audit_centre["users"]["EMPLOYEE"]
    register = save_register(admin, CashRegister(name="Caja configurable"))
    register.active = False
    save_register(admin, register)
    with pytest.raises(ValidationError, match="disponible"):
        open_session(register, employee, "20")
    register.active = True
    save_register(admin, register)
    open_session(register, employee, "20")
    register.terminal = Terminal.objects.create(code="new-terminal", name="Nueva")
    with pytest.raises(ValidationError, match="abierto"):
        save_register(admin, register)
    register.refresh_from_db()
    register.active = False
    with pytest.raises(ValidationError, match="abierto"):
        save_register(admin, register)


def test_register_http_creation_and_edit(audit_centre):
    client = admin_client(audit_centre)
    assert (
        client.post(
            reverse("cash:register_create"), {"name": "Caja HTTP", "active": "on"}
        ).status_code
        == 302
    )
    register = CashRegister.objects.get(name="Caja HTTP")
    assert (
        client.post(
            reverse("cash:register_edit", args=[register.pk]),
            {"name": "Caja archivada", "active": ""},
        ).status_code
        == 302
    )
    register.refresh_from_db()
    assert not register.active and register.name == "Caja archivada"


@pytest.mark.parametrize("role", ["EMPLOYEE", "MANAGER"])
def test_configuration_services_deny_lower_roles(audit_centre, role):
    actor = audit_centre["users"][role]
    for operation in (
        lambda: save_company_settings(actor, {"trade_name": "Denied"}),
        lambda: save_register(actor, CashRegister(name="Denied")),
        lambda: save_category(actor, Category(name="Denied")),
        lambda: save_section(actor, Section(name="Denied")),
    ):
        with pytest.raises(PermissionDenied):
            operation()


def test_terminal_preferences_apply_floor_and_cash_selector(audit_centre):
    terminal = audit_centre["terminal"]
    terminal.default_section = audit_centre["ticket"].station.section
    terminal.default_register = audit_centre["cash_session"].register
    terminal.full_clean()
    terminal.save()
    client = Client()
    client.force_login(audit_centre["users"]["EMPLOYEE"])
    session = client.session
    session["terminal_id"] = terminal.pk
    session.save()
    floor = client.get(reverse("pos:floor"))
    assert floor.status_code == 200
    assert floor.context["selected_section"] == str(terminal.default_section_id)
    response = client.get(reverse("pos:ticket", args=[audit_centre["ticket"].pk]))
    assert response.context["preferred_cash_session"] == audit_centre["cash_session"].pk
    assert client.get(reverse("pos:floor") + "?section=").context["selected_section"] == ""


def test_ordering_category_and_station_persists(audit_centre):
    admin = audit_centre["users"]["ADMIN"]
    first = save_category(admin, Category(name="Z primero", sort_order=0))
    second = save_category(admin, Category(name="A segundo", sort_order=90))
    assert list(Category.objects.filter(pk__in=[first.pk, second.pk])) == [first, second]
    station = audit_centre["ticket"].station
    station.sort_order = 71
    save_station(admin, station)
    station.refresh_from_db()
    assert station.sort_order == 71


@pytest.mark.parametrize(
    "name,param",
    [
        ("pos:floor", "section"),
        ("catalog:index", "category"),
        ("layout:index", "section"),
        ("cash:registers", "terminal"),
        ("cash:index", "register"),
    ],
)
def test_filter_ids_extreme_do_not_produce_server_error(audit_centre, name, param):
    client = admin_client(audit_centre)
    assert client.get(reverse(name), {param: "9" * 4500}).status_code == 400


def test_settings_default_get_is_categorized_commercial(audit_centre):
    response = admin_client(audit_centre).get(reverse("core:settings"))
    assert response.status_code == 200 and response.context["settings_section"] == "commercial"
    assert "trade_name" in response.context["form"].fields
    assert "tax_id" not in response.context["form"].fields
