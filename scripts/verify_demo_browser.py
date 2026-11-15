"""Real Chromium checks against an already running DEMO; never print credentials."""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.demo_config import demo_directory, read_configuration  # noqa: E402

URL = "http://127.0.0.1:8000"


def credentials(directory):
    result = {}
    current = None
    for line in (directory / "credenciales-demo.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("Usuario: "):
            current = line.split(": ", 1)[1]
            result[current] = {}
        elif current and ": " in line:
            key, value = line.split(": ", 1)
            result[current][key] = value
    return result


def verify(directory):
    from playwright.sync_api import expect, sync_playwright

    read_configuration(directory)
    users = credentials(directory)
    evidence = ROOT / "docs/evidence"
    checks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for username in ("demo_empleado", "demo_encargado", "demo_admin", "demo_superadmin"):
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            assert page.goto(URL + "/acceso/").status == 200
            if username == "demo_empleado":
                page.screenshot(path=str(evidence / "windows-demo-login.png"), full_page=True)
            page.locator("[name=username]").fill(username)
            elevated = username in ("demo_admin", "demo_superadmin")
            page.locator("[name=credential]").fill(
                users[username]["Contrasena" if elevated else "PIN"]
            )
            if elevated:
                page.locator("[name=password_mode]").check()
            page.locator("[name=terminal]").select_option(label="Terminal DEMO")
            page.get_by_role("button", name="Entrar al centro", exact=True).click()
            expect(page.get_by_role("heading", name="Plano de puestos")).to_be_visible()
            checks.append({"user": username, "login": "PASS"})
            if username == "demo_superadmin":
                for scope in ("TECHNICAL", "PII"):
                    page.goto(URL + "/soporte/")
                    form = page.locator("form").filter(has=page.locator("[name=justification]"))
                    form.locator("[name=justification]").fill(
                        "Comprobacion local de navegacion DEMO"
                    )
                    form.locator("[name=scope]").select_option(scope)
                    form.locator("[name=approver_username]").fill("demo_admin")
                    form.locator("[name=password]").fill(users["demo_admin"]["Contrasena"])
                    form.locator("button").click()
                    expect(page).to_have_url(URL + "/soporte/")
            routes = ["/tpv/", "/caja/", "/clientes/", "/facturas/"]
            if username != "demo_empleado":
                routes += ["/informes/", "/soporte/incidencias/"]
            if elevated:
                routes += [
                    "/catalogo/",
                    "/empresa/",
                    "/usuarios/",
                    "/plano/configuracion/",
                    "/auditoria/",
                ]
            if username == "demo_superadmin":
                routes += [
                    "/soporte/",
                    "/soporte/terminales/",
                    "/soporte/dispositivos/",
                    "/soporte/fiscal/",
                    "/soporte/actualizaciones/",
                ]
            for route in routes:
                response = page.goto(URL + route)
                assert response.status == 200, (username, route, response.status)
                checks.append({"user": username, "route": route, "status": 200})
            if username == "demo_empleado":
                assert page.goto(URL + "/soporte/").status == 403
                assert page.goto(URL + "/informes/").status == 403
                page.goto(URL + "/caja/")
                page.locator("#register").select_option(label="Caja DEMO")
                page.locator("#opening").fill("50.00")
                page.get_by_role("button", name="Abrir turno", exact=True).click()
                expect(page.get_by_text("Abierto", exact=True)).to_be_visible()
                page.goto(URL + "/tpv/")
                page.get_by_role("button", name="Puesto A2, libre", exact=True).click()
                page.locator(".catalog-choice").filter(has_text="Crema DEMO").get_by_role(
                    "button"
                ).click()
                expect(page.locator("#ticket-total")).to_have_text("11,00 €")
                page.goto(URL + "/tpv/")
                page.screenshot(path=str(evidence / "windows-demo-plano.png"), full_page=True)
                page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
                page.locator(".catalog-choice").filter(has_text="Manicura DEMO").get_by_role(
                    "button"
                ).click()
                page.locator("#cash-amount").fill("12.10")
                page.locator("#received").fill("20.00")
                page.locator("#cash-session").select_option(label="Caja DEMO · #1")
                expect(page.locator("#change-output")).to_contain_text("7,90")
                page.screenshot(path=str(evidence / "windows-demo-cobro.png"), full_page=True)
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("#checkout-form").get_by_role("button").click()
                expect(page).to_have_url(__import__("re").compile(r"/facturas/\d+/$"))
                expect(page.locator("body")).to_contain_text("SIN VALIDEZ FISCAL")
                page.screenshot(path=str(evidence / "windows-demo-factura.png"), full_page=True)
                checks.append(
                    {
                        "flow": "cash sale / invoice TEST / change / A2 persistent cart",
                        "result": "PASS",
                    }
                )
            if username == "demo_admin":
                assert page.goto(URL + "/soporte/").status == 403
            if username == "demo_superadmin":
                page.goto(URL + "/soporte/")
                page.screenshot(path=str(evidence / "windows-demo-soporte.png"), full_page=True)
            context.close()
        browser.close()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        with sqlite3.connect(directory / "demo.sqlite3") as db:
            print_state = db.execute(
                "SELECT status FROM hardware_printjob ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if print_state and print_state[0] == "DONE":
            break
        time.sleep(0.5)
    assert print_state and print_state[0] == "DONE"
    with sqlite3.connect(directory / "demo.sqlite3") as db:
        transmissions = db.execute("SELECT COUNT(*) FROM verifactu_fiscaltransmission").fetchone()[
            0
        ]
        invoices = db.execute(
            "SELECT COUNT(*) FROM billing_invoice WHERE fiscal_mode!='TEST'"
        ).fetchone()[0]
    assert transmissions == 0 and invoices == 0
    return {
        "date": "2026-11-15",
        "browser": "Chromium real, against Waitress localhost, DEBUG=False",
        "checks": checks,
        "simulated_receipt": "DONE (no physical device)",
        "fiscal_transmissions": transmissions,
        "non_test_invoices": invoices,
        "credentials_logged": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-dir")
    args = parser.parse_args()
    result = verify(demo_directory(args.instance_dir))
    (ROOT / "docs/evidence/windows-demo-browser.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print("Navegacion cuatro roles, cobro TEST e impresion simulada: PASS. Sin envios AEAT.")
