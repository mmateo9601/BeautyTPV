"""Consolidation flows using browser controls and a real isolated SQLite server."""

import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect
from test_audit_acceptance import authorize
from test_browser import ROOT, centre_server  # noqa: F401


def query(database, expression):
    code = (
        "import json; from apps.core.models import CompanySettings; "
        "from apps.cash.models import CashRegister; from apps.support.models import Incident; "
        "from apps.accounts.models import User; print(json.dumps(" + expression + "))"
    )
    result = subprocess.run(
        [sys.executable, "manage.py", "shell", "-c", code],
        cwd=ROOT,
        env={**os.environ, "BEAUTYTPV_DB": str(database), "BEAUTYTPV_DEBUG": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def login_role(page, address, database, role):
    result = subprocess.run(
        [
            sys.executable,
            "manage.py",
            "shell",
            "-c",
            "from apps.accounts.models import User; User.objects.filter(username='browser').update(role='"
            + role
            + "')",
        ],
        cwd=ROOT,
        env={**os.environ, "BEAUTYTPV_DB": str(database), "BEAUTYTPV_DEBUG": "1"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    page.goto(address + "/acceso/")
    page.locator("[name=username]").fill("browser")
    page.locator("[name=credential]").fill("Browser-Password-194!")
    page.locator("[name=password_mode]").check()
    page.get_by_role("button", name="Entrar al centro").click()
    expect(page.get_by_role("heading", name="Plano de puestos")).to_be_visible()


def assert_width(page):
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def evidence(page, name):
    directory = Path(ROOT) / "docs/evidence"
    directory.mkdir(exist_ok=True)
    page.screenshot(path=str(directory / name), full_page=True)


def test_admin_settings_logo_preferences_and_register_crud(page, centre_server):  # noqa: F811
    address, database = centre_server
    login_role(page, address, database, "ADMIN")
    page.get_by_role("link", name="Empresa", exact=True).click()
    page.get_by_role("link", name="Salón", exact=True).click()
    page.locator("[name=trade_name]").fill("Salón Consolidación")
    page.locator("[name=commercial_address]").fill("Local sintético de pruebas")
    page.locator("[name=phone]").fill("910000000")
    page.locator("[name=email]").fill("salon@example.test")
    page.locator("[name=ticket_footer]").fill("Gracias por tu visita")
    page.get_by_role("button", name="Guardar ajustes", exact=True).click()
    expect(page.get_by_text("Salón Consolidación", exact=True)).to_be_visible()
    assert query(database, "CompanySettings.load().trade_name") == "Salón Consolidación"
    image = io.BytesIO()
    Image.new("RGB", (80, 60), "#215b77").save(image, format="PNG")
    page.locator("[name=logo]").set_input_files(
        {"name": "logo.png", "mimeType": "image/png", "buffer": image.getvalue()}
    )
    page.get_by_role("button", name="Guardar logotipo", exact=True).click()
    assert query(database, "bool(CompanySettings.load().logo_data)")
    expect(page.get_by_alt_text("Logotipo actual")).to_be_visible()
    page.get_by_role("link", name="TPV", exact=True).click()
    page.locator("[name=theme]").select_option("ocean")
    page.locator("[name=floor_density]").select_option("compact")
    page.locator("[name=state_palette]").select_option("high_contrast")
    page.get_by_role("button", name="Guardar ajustes", exact=True).click()
    expect(page.locator("body")).to_have_class("theme-ocean density-compact palette-high_contrast")
    assert_width(page)
    evidence(page, "consolidation-settings-desktop.png")
    page.get_by_role("link", name="Cajas del centro", exact=True).click()
    create = page.locator("form").filter(has=page.locator("[name=name]"))
    create.locator("[name=name]").fill("Caja mostrador UI")
    create.locator("[name=active]").check()
    create.get_by_role("button", name="Crear caja").click()
    row = page.locator("tr").filter(has_text="Caja mostrador UI")
    expect(row).to_be_visible()
    row.get_by_role("link", name="Editar caja").click()
    page.locator("[name=active]").uncheck()
    page.get_by_role("button", name="Guardar caja").click()
    assert query(database, "CashRegister.objects.get(name='Caja mostrador UI').active") is False
    page.set_viewport_size({"width": 820, "height": 1180})
    page.get_by_role("link", name="Plano de puestos", exact=True).click()
    assert_width(page)
    evidence(page, "consolidation-floor-tablet.png")


def test_manager_incident_create_validate_and_resolve(page, centre_server):  # noqa: F811
    address, database = centre_server
    login_role(page, address, database, "MANAGER")
    page.get_by_role("link", name="Incidencias", exact=True).click()
    page.locator("[name=title]").fill("Incidencia operativa UI")
    page.locator("[name=description]").fill("cliente@example.test")
    page.locator("#id_category").select_option("OPERATIONAL")
    page.locator("#id_severity").select_option("HIGH")
    page.get_by_role("button", name="Registrar incidencia", exact=True).click()
    expect(page.locator(".field-error").first).to_contain_text("No incluya")
    assert query(database, "Incident.objects.count()") == 0
    page.locator("[name=description]").fill("El puesto necesita reorganizar el material de trabajo")
    page.get_by_role("button", name="Registrar incidencia", exact=True).click()
    if page.get_by_role("link", name="Consultar y actuar").count():
        page.get_by_role("link", name="Consultar y actuar").first.click()
    page.locator("[name=note]").fill("Material reorganizado y comprobado por el responsable")
    page.locator("[name=status]").select_option("RESOLVED")
    page.get_by_role("button", name="Guardar actuación", exact=True).click()
    expect(page.get_by_text("Resuelta", exact=True).first).to_be_visible()
    assert (
        query(database, "Incident.objects.get(title='Incidencia operativa UI').status")
        == "RESOLVED"
    )
    page.set_viewport_size({"width": 390, "height": 844})
    assert_width(page)
    evidence(page, "consolidation-incidents-mobile.png")
    page.get_by_role("link", name="INCIDENCIAS", exact=True).click()
    page.locator("[name=q]").fill("sin coincidencias")
    page.get_by_role("button", name="Filtrar", exact=True).click()
    expect(page.get_by_text("No hay incidencias con estos criterios.", exact=False)).to_be_visible()


def test_superadmin_revokes_user_session_from_team_controls(page, browser, centre_server):  # noqa: F811
    address, database = centre_server
    login_role(page, address, database, "SUPERADMIN")
    page.get_by_role("link", name="Equipo", exact=True).click()
    form = page.locator("form").filter(has=page.locator("[name=username]"))
    form.locator("[name=username]").fill("operator-ui")
    form.locator("[name=role]").select_option("EMPLOYEE")
    form.locator("[name=pin]").fill("739184")
    form.get_by_role("button", name="Crear usuario", exact=True).click()
    other_context = browser.new_context()
    try:
        employee = other_context.new_page()
        employee.goto(address + "/acceso/")
        employee.locator("[name=username]").fill("operator-ui")
        employee.locator("[name=credential]").fill("739184")
        employee.get_by_role("button", name="Entrar al centro").click()
        expect(employee.get_by_role("heading", name="Plano de puestos")).to_be_visible()
        row = page.locator("tr").filter(has_text="operator-ui")
        row.get_by_role("link", name="Editar", exact=True).click()
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="Revocar sesiones", exact=True).click()
        assert query(database, "User.objects.get(username='operator-ui').auth_version") == 1
        response = employee.goto(address + "/tpv/")
        assert response.status == 403
        authorize(page, address, "TECHNICAL")
        page.get_by_role("link", name="Gestionar incidencias", exact=True).click()
        page.locator("[name=title]").fill("Revision tecnica UI")
        page.locator("[name=description]").fill("Comprobacion de servicio sin datos personales")
        page.locator("#id_category").select_option("SYSTEM")
        page.get_by_role("button", name="Registrar incidencia", exact=True).click()
        assert (
            query(database, "Incident.objects.get(title='Revision tecnica UI').category")
            == "SYSTEM"
        )
    finally:
        other_context.close()


def test_admin_category_visibility_reaches_real_pos_and_cart(page, centre_server):  # noqa: F811
    address, database = centre_server
    login_role(page, address, database, "ADMIN")
    page.get_by_role("link", name="Catálogo", exact=True).click()
    page.get_by_role("link", name="Gestionar categorias", exact=True).click()
    page.locator("#id_name").fill("Categoria UI temporal")
    page.locator("#id_sort_order").fill("10")
    page.locator("#id_visible_in_pos").uncheck()
    page.get_by_role("button", name="Guardar categoria", exact=True).click()
    page.get_by_role("link", name="VOLVER AL CATALOGO", exact=True).click()
    page.get_by_role("link", name="+ Nuevo artículo", exact=True).click()
    page.locator("#id_name").fill("Servicio visibilidad UI")
    page.locator("#id_category").select_option(label="Categoria UI temporal")
    page.locator("#id_price").fill("9.99")
    page.locator("#id_tax_rate").fill("21")
    page.locator("#id_sort_order").fill("3")
    page.get_by_role("button", name="Guardar artículo", exact=True).click()
    page.get_by_role("link", name="Plano de puestos", exact=True).click()
    page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
    expect(
        page.locator(".catalog-choice").filter(has_text="Servicio visibilidad UI")
    ).to_have_count(0)
    ticket_url = page.url
    page.get_by_role("link", name="Catálogo", exact=True).click()
    page.get_by_role("link", name="Gestionar categorias", exact=True).click()
    page.get_by_role("link", name="Categoria UI temporal", exact=True).click()
    page.locator("#id_visible_in_pos").check()
    page.get_by_role("button", name="Guardar categoria", exact=True).click()
    page.goto(ticket_url)
    page.locator(".catalog-choice").filter(has_text="Servicio visibilidad UI").get_by_role(
        "button"
    ).click()
    expect(page.locator("#ticket-total")).to_have_text("9,99 €")
    page.locator("[name=note]").fill("Nota operativa UI")
    page.locator("form.line-edit").get_by_role("button", name="Guardar", exact=True).click()
    expect(page.get_by_text("Nota operativa UI", exact=True)).to_be_visible()
    page.set_viewport_size({"width": 390, "height": 844})
    assert_width(page)
    evidence(page, "consolidation-ticket-mobile.png")
    page.get_by_role("link", name="← VOLVER AL PLANO", exact=True).click()
    expect(page.locator(".station-card").filter(has_text="A1")).to_contain_text("9,99 €")
