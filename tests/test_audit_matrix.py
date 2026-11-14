"""Independent route/role audit. Every route must have an explicit test policy.

PKs refer to real fixture objects, so authorization is not confused with a 404.
The matrix deliberately does not claim that invalid-form POSTs prove each business flow.
Those flows are exercised separately by the acceptance suites and browser tests.
"""

import hashlib
import io
import json
from dataclasses import dataclass
from datetime import timedelta
from html.parser import HTMLParser
from pathlib import Path

import pytest
from django.test import Client
from django.urls import URLResolver, get_resolver, reverse
from django.utils import timezone
from PIL import Image

from apps.accounts.models import User
from apps.accounts.permissions import ROLE_RANK
from apps.cash.models import CashRegister
from apps.cash.services import open_session
from apps.catalog.models import CatalogItem, Category
from apps.core.models import CompanySettings, Terminal
from apps.customers.models import Customer
from apps.hardware.models import Printer
from apps.layout.models import Section, Station
from apps.pos.services import add_line, checkout, open_ticket
from apps.support.models import BackupRun, Incident, SupportSession


@dataclass(frozen=True)
class Policy:
    minimum: str
    method: str = "GET"
    object: str = ""


POLICIES = {
    "<root>": Policy("PUBLIC"),
    "health": Policy("PUBLIC"),
    "accounts:login": Policy("PUBLIC"),
    "accounts:logout": Policy("PUBLIC", "POST"),
    "accounts:elevate": Policy("AUTHENTICATED"),
    "audit:index": Policy("ADMIN"),
    "pos:floor": Policy("EMPLOYEE"),
    "pos:quick_sale": Policy("EMPLOYEE", "POST"),
    "pos:open_station": Policy("EMPLOYEE", "POST", "station"),
    "pos:ticket": Policy("EMPLOYEE", object="ticket"),
    "pos:prepare_payment": Policy("EMPLOYEE", "POST", "ticket"),
    "pos:resume_ticket": Policy("EMPLOYEE", "POST", "ticket"),
    "pos:add_line": Policy("EMPLOYEE", "POST", "ticket"),
    "pos:update_line": Policy("EMPLOYEE", "POST", "line"),
    "pos:remove_line": Policy("MANAGER", "POST", "line"),
    "pos:cancel_ticket": Policy("MANAGER", "POST", "ticket"),
    "pos:customer": Policy("EMPLOYEE", "POST", "ticket"),
    "pos:checkout": Policy("EMPLOYEE", "POST", "ticket"),
    "layout:index": Policy("ADMIN"),
    "layout:section_create": Policy("ADMIN", "POST"),
    "layout:section_edit": Policy("ADMIN", object="section"),
    "layout:section_delete": Policy("ADMIN", "POST", "section"),
    "layout:station_create": Policy("ADMIN"),
    "layout:station_edit": Policy("ADMIN", object="station"),
    "layout:station_delete": Policy("ADMIN", "POST", "station"),
    "catalog:index": Policy("ADMIN"),
    "catalog:create": Policy("ADMIN"),
    "catalog:edit": Policy("ADMIN", object="item"),
    "catalog:category": Policy("ADMIN"),
    "catalog:category_edit": Policy("ADMIN", object="category"),
    "catalog:category_delete": Policy("ADMIN", "POST", "category"),
    "customers:index": Policy("EMPLOYEE"),
    "customers:create": Policy("EMPLOYEE"),
    "customers:detail": Policy("EMPLOYEE", object="customer"),
    "customers:edit": Policy("EMPLOYEE", object="customer"),
    "customers:delete": Policy("ADMIN", "POST", "customer"),
    "cash:index": Policy("EMPLOYEE"),
    "cash:registers": Policy("ADMIN"),
    "cash:register_create": Policy("ADMIN", "POST"),
    "cash:register_edit": Policy("ADMIN", object="register"),
    "cash:open": Policy("EMPLOYEE", "POST"),
    "cash:movement": Policy("MANAGER", "POST", "cash_session"),
    "cash:close": Policy("MANAGER", "POST", "cash_session"),
    "billing:index": Policy("EMPLOYEE"),
    "billing:list": Policy("EMPLOYEE"),
    "billing:detail": Policy("EMPLOYEE", object="invoice"),
    "billing:pdf": Policy("EMPLOYEE", object="invoice"),
    "billing:rectify": Policy("MANAGER", "POST", "invoice"),
    "billing:reprint": Policy("EMPLOYEE", "POST", "invoice"),
    "hardware:reprint": Policy("EMPLOYEE", "POST", "invoice"),
    "hardware:test": Policy("SUPERADMIN", "POST", "printer"),
    "hardware:retry": Policy("SUPERADMIN", "POST", "job"),
    "hardware:bridge_claim": Policy("BRIDGE", "POST"),
    "hardware:bridge_ack": Policy("BRIDGE", "POST"),
    "core:settings": Policy("ADMIN"),
    "core:logo": Policy("EMPLOYEE"),
    "core:logo_save": Policy("ADMIN", "POST"),
    "reports:index": Policy("MANAGER"),
    "support:index": Policy("SUPERADMIN"),
    "support:incidents": Policy("MANAGER"),
    "support:incident_detail": Policy("MANAGER", object="incident"),
    "support:authorize": Policy("SUPERADMIN", "POST"),
    "support:revoke": Policy("SUPERADMIN", "POST", "authorization"),
    "support:diagnostic": Policy("SUPERADMIN", "POST"),
    "support:diagnostics_export": Policy("SUPERADMIN"),
    "support:backup": Policy("SUPERADMIN", "POST"),
    "support:backup_download": Policy("SUPERADMIN", object="backup"),
    "support:backup_verify": Policy("SUPERADMIN", "POST", "backup"),
    "support:printer_save": Policy("SUPERADMIN"),
    "support:printer_edit": Policy("SUPERADMIN", object="printer"),
    "support:recover_fiscal": Policy("SUPERADMIN", "POST", "outbox"),
    "support:correct_fiscal": Policy("SUPERADMIN", "POST", "outbox"),
    "support:annul_fiscal": Policy("SUPERADMIN", "POST", "outbox"),
    "support:settings": Policy("SUPERADMIN"),
    "support:updates": Policy("SUPERADMIN"),
    "support:logs": Policy("SUPERADMIN"),
    "support:terminals": Policy("SUPERADMIN"),
    "support:terminal_edit": Policy("SUPERADMIN", object="terminal"),
    "support:fiscal_settings": Policy("SUPERADMIN"),
    "support:restore_advisor": Policy("SUPERADMIN"),
    "team:index": Policy("ADMIN"),
    "team:edit": Policy("ADMIN", object="employee"),
    "team:unlock": Policy("ADMIN", "POST", "employee"),
    "team:revoke_sessions": Policy("ADMIN", "POST", "employee"),
}


def route_names(patterns=None, namespace=""):
    for pattern in patterns or get_resolver().url_patterns:
        if isinstance(pattern, URLResolver):
            yield from route_names(
                pattern.url_patterns,
                namespace + (pattern.namespace + ":" if pattern.namespace else ""),
            )
        else:
            yield namespace + (pattern.name or "<root>")


@pytest.fixture
def audit_centre(db, settings, tmp_path, monkeypatch):
    settings.DEBUG = True
    settings.HARDWARE_SIMULATOR = True
    settings.FISCAL_PRODUCER = {"name": "Productor auditoría", "tax_id": "89890001K"}
    monkeypatch.setenv("BEAUTYTPV_BACKUP_DIR", str(tmp_path))
    monkeypatch.delenv("BEAUTYTPV_BACKUP_KEY", raising=False)
    users = {
        role: User.objects.create_user(username="matrix-" + role.lower(), role=role)
        for role in User.Role.values
    }
    employee = users["EMPLOYEE"]
    company = CompanySettings.load()
    company.name = "Centro auditoría"
    company.tax_id = "89890001K"
    company.address = "Auditoría 1"
    image = io.BytesIO()
    Image.new("RGB", (1, 1), "white").save(image, "PNG")
    company.logo_data = image.getvalue()
    company.save()
    terminal = Terminal.objects.create(code="matrix", name="Terminal auditoría")
    section = Section.objects.create(name="M")
    station = Station.objects.create(section=section, code="M1", name="Puesto auditoría")
    sold_station = Station.objects.create(section=section, code="M2", name="Puesto emitido")
    category = Category.objects.create(name="Categoría auditoría")
    item = CatalogItem.objects.create(
        name="Servicio auditoría", price="12.10", tax_rate="21", category=category
    )
    customer = Customer.objects.create(name="Cliente auditoría sin historial")
    cash_session = open_session(CashRegister.objects.create(name="Caja auditoría"), employee, "50")
    register = cash_session.register
    incident = Incident.objects.create(
        title="Incidencia operativa de auditoría",
        description="Comprobación sin datos personales",
        created_by=users["MANAGER"],
    )
    printer = Printer.objects.create(name="Simulador auditoría", connection_type="SIMULATOR")
    issued = open_ticket(sold_station, employee)
    add_line(issued, item, employee)
    sale = checkout(
        issued,
        employee,
        [{"method": "CARD", "amount": "12.10", "reference": "AUDIT-CONFIRMED"}],
        "matrix-issued",
    )
    invoice = sale.invoice
    outbox = invoice.fiscal_records.get().outbox
    job = invoice.print_jobs.get()
    ticket = open_ticket(station, employee)
    line = add_line(ticket, item, employee)
    authorizations = {}
    for scope in ("TECHNICAL", "PII", "BACKUP", "UPDATE"):
        authorizations[scope] = SupportSession.objects.create(
            actor=users["SUPERADMIN"],
            approved_by=users["ADMIN"],
            justification="Auditoría de permisos autorizada con datos sintéticos",
            scope=scope,
            expires_at=timezone.now() + timedelta(minutes=20),
        )
    authorization = authorizations["TECHNICAL"]
    payload = b"Synthetic encrypted-backup download fixture, not a production backup"
    archive = tmp_path / "matrix.btpv"
    archive.write_bytes(payload)
    backup = BackupRun.objects.create(
        filename=archive.name,
        sha256=hashlib.sha256(payload).hexdigest(),
        created_by=users["SUPERADMIN"],
    )
    return locals()


def location(name, fixture):
    if name == "<root>":
        return "/"
    if name.startswith("hardware:bridge_"):
        values = {"terminal_pk": fixture["terminal"].pk}
        if name == "hardware:bridge_ack":
            values["job_pk"] = fixture["job"].pk
        return reverse(name, kwargs=values)
    policy = POLICIES[name]
    return reverse(name, kwargs={"pk": fixture[policy.object].pk} if policy.object else None)


def signed_client(fixture, role, *, elevated=True):
    client = Client(raise_request_exception=False)
    if role != "ANONYMOUS":
        client.force_login(fixture["users"][role])
        session = client.session
        if elevated:
            session["elevated_until"] = timezone.now().timestamp() + 600
        session.save()
    return client


def test_all_live_routes_and_baseline_have_explicit_audit_policy():
    current = set(route_names())
    assert current <= POLICIES.keys(), (
        f"Routes missing QA contract: {sorted(current - POLICIES.keys())}"
    )
    baseline = json.loads(
        (Path(__file__).resolve().parents[1] / "docs/audit/baseline/inventory.json").read_text(
            encoding="utf-8"
        )
    )
    names = {
        route["name"] if route["name"] != "<unnamed>" else "<root>" for route in baseline["routes"]
    }
    assert names <= POLICIES.keys()


@pytest.mark.parametrize("name", sorted(set(route_names())))
@pytest.mark.parametrize("role", ["ANONYMOUS", *User.Role.values])
def test_every_route_role_authorization(name, role, audit_centre):
    policy = POLICIES[name]
    client = signed_client(audit_centre, role)
    data = {
        "version": "-1",
        "idempotency_key": "invalid-audit",
        "cash_amount": "not-money",
        "counted": "not-money",
    }
    response = getattr(client, policy.method.lower())(location(name, audit_centre), data)
    permitted = policy.minimum == "PUBLIC" or (
        role != "ANONYMOUS"
        and policy.minimum != "BRIDGE"
        and (policy.minimum == "AUTHENTICATED" or ROLE_RANK[role] >= ROLE_RANK[policy.minimum])
    )
    if not permitted:
        assert response.status_code == 403 or (
            role == "ANONYMOUS"
            and response.status_code == 302
            and response.headers.get("Location", "").startswith("/acceso/")
        ), (name, role, response.status_code, response.content[:200])
    else:
        assert response.status_code in {200, 302, 400, 409}, (
            name,
            role,
            response.status_code,
            response.content[:200],
        )
        if policy.method == "GET" and name != "<root>":
            assert response.status_code == 200, (name, role, response.status_code)


@pytest.mark.parametrize("role", ["ADMIN", "SUPERADMIN"])
def test_administrative_get_routes_require_elevation(role, audit_centre):
    client = signed_client(audit_centre, role, elevated=False)
    for name, policy in POLICIES.items():
        if name not in set(route_names()) or policy.method != "GET":
            continue
        if (
            policy.minimum in ("ADMIN", "SUPERADMIN")
            and ROLE_RANK[role] >= ROLE_RANK[policy.minimum]
        ):
            response = client.get(location(name, audit_centre))
            assert response.status_code == 403, (name, role, response.status_code)


def test_superadmin_pii_needs_an_independent_active_approver(audit_centre):
    client = signed_client(audit_centre, "SUPERADMIN")
    pii = audit_centre["authorizations"]["PII"]
    pii.approved_by = audit_centre["users"]["SUPERADMIN"]
    pii.save()
    for url in ("/clientes/", "/facturas/", "/informes/", location("pos:ticket", audit_centre)):
        assert client.get(url).status_code == 403
    pii.approved_by = audit_centre["users"]["ADMIN"]
    pii.save()
    assert client.get("/clientes/").status_code == 200
    pii.revoked_at = timezone.now()
    pii.save()
    assert client.get("/clientes/").status_code == 403


class MenuLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_nav = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "nav":
            self.in_nav = True
        if tag == "a" and self.in_nav:
            self.links.append(dict(attrs).get("href", ""))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False


@pytest.mark.parametrize("role", User.Role.values)
def test_every_visible_menu_link_is_authorized_for_its_role(role, audit_centre):
    client = signed_client(audit_centre, role)
    response = client.get("/tpv/")
    assert response.status_code == 200
    menu = MenuLinks()
    menu.feed(response.content.decode())
    assert menu.links
    for url in menu.links:
        if url.startswith("/"):
            linked = client.get(url)
            assert linked.status_code == 200, (role, url, linked.status_code)


@pytest.mark.parametrize(
    "name",
    sorted(
        name
        for name, policy in POLICIES.items()
        if policy.method == "POST" and policy.minimum != "BRIDGE"
    ),
)
def test_cookie_authenticated_mutations_reject_missing_csrf(name, audit_centre):
    if name not in set(route_names()):
        pytest.skip("Policy reserved for a coordinated route not yet registered")
    client = Client(enforce_csrf_checks=True)
    client.force_login(audit_centre["users"]["SUPERADMIN"])
    assert client.post(location(name, audit_centre), {}).status_code == 403
