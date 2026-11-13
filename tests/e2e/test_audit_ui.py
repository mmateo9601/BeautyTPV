"""Browser regressions for the second UI audit; real Django and SQLite."""

import os
import subprocess
import sys

import pytest
from playwright.sync_api import expect
from test_browser import ROOT, centre_server, login_pin  # noqa: F401, F811


def test_pending_payment_blocks_editing_and_retains_note(page, centre_server):  # noqa: F811
    address, _ = centre_server
    login_pin(page, address)
    page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
    expect(page.locator("#catalog-category")).to_be_visible()
    page.locator(".catalog-choice button").click()
    page.locator(".cart-line [name=note]").fill("Preferencia del servicio")
    page.locator(".cart-line").get_by_role("button", name="Guardar", exact=True).click()
    page.get_by_role("button", name="Preparar cobro y bloquear edici\u00f3n").click()
    expect(page.get_by_text("Cuenta en cobro.", exact=True)).to_be_visible()
    expect(page.locator(".catalog-choice")).to_have_count(0)
    expect(page.locator(".line-edit")).to_have_count(0)
    expect(page.locator("#checkout-form")).to_be_visible()
    expect(page.get_by_text("Preferencia del servicio", exact=True)).to_be_visible()
    page.goto(address + "/tpv/")
    expect(page.locator(".station-card.is-pending")).to_have_count(1)
    with page.expect_response(
        lambda response: response.request.headers.get("hx-request") == "true"
    ) as refresh:
        page.get_by_role("button", name="Actualizar plano", exact=True).click()
    assert refresh.value.status == 200
    expect(page.locator(".station-card.is-pending")).to_have_count(1)
    page.get_by_role("button", name="Puesto A1, cuenta abierta", exact=True).click()
    page.get_by_role("button", name="Volver a editar cuenta", exact=True).click()
    expect(page.locator(".cart-line [name=note]")).to_have_value("Preferencia del servicio")
    expect(page.locator(".catalog-choice")).to_have_count(1)


@pytest.mark.parametrize(
    "role,management,admin,support",
    [
        ("EMPLOYEE", False, False, False),
        ("MANAGER", True, False, False),
        ("ADMIN", True, True, False),
        ("SUPERADMIN", True, True, True),
    ],
)
def test_role_navigation_and_mobile_layout(page, centre_server, role, management, admin, support):  # noqa: F811
    address, database = centre_server
    command = f"from apps.accounts.models import User; User.objects.filter(username='browser').update(role={role!r})"
    completed = subprocess.run(
        [sys.executable, "manage.py", "shell", "-c", command],
        cwd=ROOT,
        env={**os.environ, "BEAUTYTPV_DB": str(database), "BEAUTYTPV_DEBUG": "1"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    if role in {"ADMIN", "SUPERADMIN"}:
        page.goto(address + "/acceso/")
        page.locator("[name=username]").fill("browser")
        page.locator("[name=credential]").fill("Browser-Password-194!")
        page.locator("[name=password_mode]").check()
        page.get_by_role("button", name="Entrar al centro").click()
    else:
        login_pin(page, address)
    nav = page.get_by_role("navigation", name="Principal")
    expect(nav.get_by_role("link", name="Informes", exact=True)).to_have_count(int(management))
    expect(nav.get_by_role("link", name="Cat\u00e1logo", exact=True)).to_have_count(int(admin))
    expect(nav.get_by_role("link", name="Soporte t\u00e9cnico", exact=True)).to_have_count(
        int(support)
    )
    footer = page.locator(".sidebar-user").bounding_box()
    assert footer and footer["y"] + footer["height"] <= page.viewport_size["height"] + 1
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    expect(page.get_by_role("heading", name="Plano de puestos")).to_be_visible()
    if support:
        response = page.goto(address + "/informes/")
        assert response.status == 403
        expect(page.locator("body")).to_contain_text("PII")
    elif management:
        page.goto(address + "/informes/")
        expect(page).to_have_title("Informes \u00b7 BeautyTPV")
        expect(page.get_by_role("heading", name="Por empleado")).to_have_count(1)
