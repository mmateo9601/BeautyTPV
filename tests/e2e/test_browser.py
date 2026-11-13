"""Actual browser against an isolated Django process and persistent SQLite file.

Run on Windows with a browser-permitted process. No business/network mocks are used.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[2]
DRIVER = Path(__file__).with_name("sqlite_process.py")
EVIDENCE = ROOT / "docs/evidence"


def inspect_database(database):
    result = subprocess.run(
        [sys.executable, str(DRIVER), json.dumps({"action": "inspect"})],
        env={**os.environ, "BEAUTYTPV_DB": str(database), "BEAUTYTPV_DEBUG": "1"},
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.fixture
def centre_server(tmp_path):
    database = tmp_path / "browser.sqlite3"
    env = {**os.environ, "BEAUTYTPV_DB": str(database), "BEAUTYTPV_DEBUG": "1"}
    result = subprocess.run(
        [sys.executable, str(DRIVER), json.dumps({"action": "seed", "open_cash": False})],
        env=env,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    address = f"http://127.0.0.1:{port}"
    log_file = tmp_path / "server.log"
    with log_file.open("w", encoding="utf-8") as logs:
        process = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
            cwd=ROOT,
            env=env,
            stdout=logs,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    with urllib.request.urlopen(address + "/health/", timeout=1) as response:
                        if response.status == 200:
                            break
                except (OSError, urllib.error.URLError):
                    if process.poll() is not None or time.monotonic() >= deadline:
                        pytest.fail(log_file.read_text(encoding="utf-8"))
                    time.sleep(0.1)
            yield address, database
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def login_pin(page, address):
    page.goto(address + "/acceso/")
    page.get_by_label(re.compile(r"^Usuario:?$")).fill("browser")
    page.get_by_label(re.compile(r"^PIN o contraseña:?$")).fill("827364")
    page.get_by_role("button", name="Entrar al centro").click()
    expect(page.get_by_role("heading", name="Plano de puestos")).to_be_visible()


def test_e01_browser_pin_cash_invoice_copy_report_and_close(page, centre_server):
    address, database = centre_server
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    login_pin(page, address)
    page.goto(address + "/caja/")
    page.locator("#opening").fill("50.00")
    page.get_by_role("button", name="Abrir turno", exact=True).click()
    expect(page.get_by_text("Abierto", exact=True)).to_be_visible()
    page.goto(address + "/tpv/")
    page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
    page.locator(".catalog-choice").filter(has_text="Manicura QA").get_by_role("button").click()
    expect(page.locator("#ticket-total")).to_have_text("12,10 €")
    page.locator("#cash-amount").fill("12.10")
    page.locator("#received").fill("20.00")
    page.locator("#cash-session").select_option(index=1)
    expect(page.locator("#change-output")).to_contain_text("7,90")
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#checkout-form").get_by_role("button").click()
    expect(page).to_have_url(re.compile(r"/facturas/\d+/$"))
    expect(
        page.get_by_text("ENTORNO DE PRUEBAS · SIN VALIDEZ FISCAL PRODUCTIVA", exact=True).first
    ).to_be_visible()
    expect(page.get_by_role("link", name="Abrir verificación QR en AEAT")).to_have_attribute(
        "href", re.compile(r"https://prewww2.aeat.es/.+ValidarQR")
    )
    pdf_url = page.get_by_role("link", name="Descargar PDF").get_attribute("href")
    response = page.request.get(address + pdf_url)
    assert response.status == 200 and response.body().startswith(b"%PDF")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "invoice-test.pdf").write_bytes(response.body())
    page.get_by_role("button", name="Imprimir copia", exact=True).click()
    expect(page.get_by_text("Copia enviada a cola de impresión.", exact=True)).to_be_visible()
    state = inspect_database(database)
    assert state["sales"] == state["records"] == 1
    assert state["print_jobs"] == 2 and state["copies"] == 1
    assert Decimal(state["cash"][0]["expected"]) == Decimal("62.10")
    assert state["chain_valid"]
    page.goto(address + "/informes/")
    expect(page.get_by_role("heading", name="Informes de ventas")).to_be_visible()
    expect(page.locator("body")).to_contain_text("12,10")
    page.goto(address + "/caja/")
    page.get_by_label("Efectivo contado (€)").fill("62.10")
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Cerrar turno", exact=True).click()
    expect(page.get_by_text("Cerrado", exact=True)).to_be_visible()
    state = inspect_database(database)
    assert state["cash"][0]["closed"] and Decimal(state["cash"][0]["difference"]) == 0
    assert not errors, errors


def test_e02_browser_accounts_survive_navigation_and_new_browser_session(browser, centre_server):
    address, database = centre_server
    context = browser.new_context()
    page = context.new_page()
    try:
        login_pin(page, address)
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.screenshot(path=str(EVIDENCE / "floor-desktop.png"), full_page=True)
        page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
        page.locator(".catalog-choice").filter(has_text="Manicura QA").get_by_role("button").click()
        first_url = page.url
        page.get_by_role("link", name="← VOLVER AL PLANO").click()
        page.get_by_role("button", name="Puesto A2, libre", exact=True).click()
        expect(page.locator("#ticket-total")).to_have_text("0,00 €")
        page.goto(address + "/tpv/")
        page.get_by_role("button", name="Puesto A1, cuenta abierta", exact=True).click()
        assert page.url == first_url
        expect(page.locator("#ticket-total")).to_have_text("12,10 €")
        page.set_viewport_size({"width": 900, "height": 1180})
        page.screenshot(path=str(EVIDENCE / "ticket-tablet.png"), full_page=True)
    finally:
        context.close()
    context = browser.new_context()
    try:
        page = context.new_page()
        login_pin(page, address)
        page.get_by_role("button", name="Puesto A1, cuenta abierta", exact=True).click()
        expect(page.locator("#ticket-total")).to_have_text("12,10 €")
        expect(page.locator(".cart-line")).to_have_count(1)
    finally:
        context.close()
    state = inspect_database(database)
    assert state["tickets"]["A1"]["lines"] == 1 and state["tickets"]["A2"]["lines"] == 0


def test_e03_e16_browser_catalog_customer_full_invoice_and_snapshot(page, centre_server):
    address, database = centre_server
    page.goto(address + "/acceso/")
    page.locator("[name=username]").fill("browser-admin")
    page.locator("[name=credential]").fill("Browser-Admin-Password-194!")
    page.locator("[name=password_mode]").check()
    page.get_by_role("button", name="Entrar al centro").click()
    expect(page.get_by_role("heading", name="Plano de puestos")).to_be_visible()
    page.goto(address + "/catalogo/")
    page.get_by_role("link", name="+ Nuevo artículo").click()
    page.locator("[name=kind]").select_option("PRODUCT")
    page.locator("[name=name]").fill("Producto IVA10 QA")
    page.locator("[name=price]").fill("11.00")
    page.locator("[name=tax_rate]").fill("10.00")
    page.locator("[name=active]").check()
    page.get_by_role("button", name="Guardar artículo").click()
    product_row = page.locator("tr").filter(has_text="Producto IVA10 QA")
    expect(product_row).to_be_visible()
    edit_url = product_row.get_by_role("link", name="Editar", exact=True).get_attribute("href")
    page.goto(address + "/clientes/")
    page.get_by_role("link", name="+ Nuevo cliente").click()
    for field, value in {
        "name": "Cliente QA con factura",
        "phone": "600000001",
        "email": "qa@example.invalid",
        "tax_id": "89890001K",
        "address": "Dirección QA 1",
    }.items():
        page.locator(f"[name={field}]").fill(value)
    page.get_by_role("button", name="Guardar ficha").click()
    expect(page.get_by_role("heading", name="Cliente QA con factura", exact=True)).to_be_visible()
    customer_url = page.url
    page.goto(address + "/tpv/")
    page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
    page.locator("#ticket-customer").select_option(label="Cliente QA con factura")
    page.get_by_role("button", name="Asignar", exact=True).click()
    page.locator(".catalog-choice").filter(has_text="Producto IVA10 QA").get_by_role(
        "button"
    ).click()
    page.locator(".cart-line [name=discount_percent]").fill("10")
    page.locator(".cart-line").get_by_role("button", name="Guardar", exact=True).click()
    expect(page.locator("#ticket-total")).to_have_text("9,90 €")
    page.locator("#card-amount").fill("9.90")
    page.locator("#card-reference").fill("CONFIRMED-EXTERNAL-QA")
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#checkout-form").get_by_role("button").click()
    expect(page).to_have_url(re.compile(r"/facturas/\d+/$"))
    expect(page.get_by_role("heading", name="Cliente QA con factura", exact=True)).to_be_visible()
    expect(page.locator("body")).to_contain_text("F1")
    invoice_url = page.url
    page.goto(address + edit_url)
    page.locator("[name=price]").fill("99.99")
    page.get_by_role("button", name="Guardar artículo").click()
    page.goto(invoice_url)
    expect(page.locator(".cart-total strong")).to_have_text("9,90 €")
    page.goto(customer_url)
    expect(page.get_by_role("heading", name="Historial de compras")).to_be_visible()
    expect(page.get_by_role("link", name=re.compile(r"F-\d{4}-000001"))).to_be_visible()
    assert inspect_database(database)["sales"] == 1
