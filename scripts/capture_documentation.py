"""Capture real documentation screens in a disposable, offline DEMO.

Never connects to port 8000 or reads the user's existing DEMO credentials.
Screenshots are unaltered Chromium viewport captures; PNG optimisation is lossless.
"""

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.demo_config import demo_environment  # noqa: E402
from scripts.demo_server import WindowsEvent  # noqa: E402


def serve(directory, port, token):
    os.environ.update(demo_environment(directory))
    import django

    django.setup()
    from django.core.wsgi import get_wsgi_application
    from waitress import create_server

    from scripts.demo_server import (
        DemoIdentityApplication,
        install_network_guard,
        validate_demo_database,
        worker_loop,
    )
    from scripts.service import close_server

    validate_demo_database(directory)
    install_network_guard()
    stop = threading.Event()
    with WindowsEvent(token) as signal:
        server = create_server(
            DemoIdentityApplication(get_wsgi_application(), token),
            host="127.0.0.1",
            port=port,
            threads=4,
            asyncore_loop_timeout=0.5,
        )

        def close():
            close_server(server)

        def monitor():
            while not stop.is_set():
                if signal.wait(0.2):
                    stop.set()
                    close()

        worker = threading.Thread(target=worker_loop, args=(stop, close), daemon=True)
        watcher = threading.Thread(target=monitor, daemon=True)
        worker.start()
        watcher.start()
        try:
            server.run()
        finally:
            stop.set()
            watcher.join(timeout=3)
            worker.join(timeout=5)
            close()


def capture(output):
    from PIL import Image
    from playwright.sync_api import expect, sync_playwright

    from scripts.verify_demo_browser import credentials
    from scripts.windows_demo import setup_demo

    output.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="beautytpv-documentation-") as temporary:
        directory = Path(temporary) / "BeautyTPV-DEMO"
        setup_demo(directory)
        users = credentials(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert port != 8000
        address = f"http://127.0.0.1:{port}"
        token = secrets.token_hex(32)
        with (directory / "capture-server.log").open("w", encoding="utf-8") as logs:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--serve",
                    "--instance-dir",
                    str(directory),
                    "--port",
                    str(port),
                    "--token",
                    token,
                ],
                cwd=ROOT,
                env=demo_environment(directory),
                stdout=logs,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 40
                while True:
                    try:
                        request = urllib.request.Request(
                            address + "/__demo_ready__", headers={"X-BeautyTPV-Demo": token}
                        )
                        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                            request, timeout=1
                        ) as response:
                            assert (
                                json.load(response)["identity"]
                                == hashlib.sha256(token.encode()).hexdigest()
                            )
                        break
                    except OSError:
                        if process.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError(
                                "Documentation DEMO did not start; inspect temporary sanitized log"
                            ) from None
                        time.sleep(0.2)
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()

                    def shot(page, filename, role, description, anchor=None):
                        if anchor:
                            anchor.scroll_into_view_if_needed()
                        page.screenshot(path=str(output / filename), full_page=False)
                        with Image.open(output / filename) as picture:
                            picture.save(output / filename, optimize=True)
                        records.append(
                            {
                                "file": filename,
                                "role": role,
                                "route": page.url.removeprefix(address),
                                "viewport": dict(page.viewport_size),
                                "description": description,
                                "sha256": hashlib.sha256(
                                    (output / filename).read_bytes()
                                ).hexdigest(),
                                "bytes": (output / filename).stat().st_size,
                            }
                        )

                    def login(username):
                        context = browser.new_context(
                            viewport={"width": 1440, "height": 900}, locale="es-ES"
                        )
                        page = context.new_page()
                        page.goto(address + "/acceso/")
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
                        return context, page

                    context = browser.new_context(
                        viewport={"width": 1440, "height": 900}, locale="es-ES"
                    )
                    page = context.new_page()
                    page.goto(address + "/acceso/")
                    shot(
                        page,
                        "login-desktop.png",
                        "PUBLIC",
                        "Identificación, campos vacíos y aviso TEST",
                    )
                    page.get_by_role("button", name="demo_empleado", exact=True).click()
                    shot(
                        page,
                        "selector-pin-desktop.png",
                        "PUBLIC",
                        "Selector táctil de usuario; PIN vacío",
                    )
                    context.close()

                    context, page = login("demo_empleado")
                    shot(
                        page,
                        "plano-salon-desktop.png",
                        "EMPLOYEE",
                        "Plano inicial, cuatro puestos libres",
                    )
                    shot(
                        page,
                        "puesto-libre-desktop.png",
                        "EMPLOYEE",
                        "El puesto libre se representa en el plano; no hay modal separado",
                    )
                    for width, height, suffix in ((820, 1180, "tablet"), (390, 844, "mobile")):
                        page.set_viewport_size({"width": width, "height": height})
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        )
                        shot(page, f"plano-salon-{suffix}.png", "EMPLOYEE", "Plano responsive real")
                    page.set_viewport_size({"width": 1440, "height": 900})
                    page.goto(address + "/caja/")
                    page.locator("#register").select_option(label="Caja DEMO")
                    page.locator("#opening").fill("50.00")
                    page.get_by_role("button", name="Abrir turno", exact=True).click()
                    shot(
                        page,
                        "caja-desktop.png",
                        "EMPLOYEE",
                        "Turno real abierto con fondo sintético",
                    )
                    page.goto(address + "/tpv/")
                    page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
                    page.locator(".catalog-choice").filter(has_text="Manicura DEMO").get_by_role(
                        "button"
                    ).click()
                    page.locator(".cart-line [name=note]").fill(
                        "Preferencia sintética: tono natural"
                    )
                    page.locator(".cart-line").get_by_role(
                        "button", name="Guardar", exact=True
                    ).click()
                    expect(page.locator("#ticket-total")).to_have_text("12,10 €")
                    shot(
                        page,
                        "cuenta-puesto-desktop.png",
                        "EMPLOYEE",
                        "Cuenta abierta con línea y nota persistida",
                    )
                    shot(
                        page, "carrito-desktop.png", "EMPLOYEE", "Carrito de una cuenta persistente"
                    )
                    page.set_viewport_size({"width": 820, "height": 1180})
                    shot(page, "cuenta-puesto-tablet.png", "EMPLOYEE", "Cuenta en tablet")
                    page.set_viewport_size({"width": 390, "height": 844})
                    shot(
                        page,
                        "cuenta-puesto-mobile.png",
                        "EMPLOYEE",
                        "Cuenta estrecha; continuación mediante scroll",
                    )
                    page.set_viewport_size({"width": 1440, "height": 900})
                    page.locator("#cash-amount").fill("12.10")
                    page.locator("#received").fill("20.00")
                    page.locator("#cash-session").select_option(label="Caja DEMO · #1")
                    expect(page.locator("#change-output")).to_contain_text("7,90")
                    shot(
                        page,
                        "cobro-efectivo.png",
                        "EMPLOYEE",
                        "Cobro sintético antes de confirmar; cambio7,90",
                        page.locator("#checkout-form"),
                    )
                    page.set_viewport_size({"width": 390, "height": 844})
                    shot(
                        page,
                        "cobro-mobile.png",
                        "EMPLOYEE",
                        "Controles de cobro estrechos",
                        page.locator("#checkout-form"),
                    )
                    page.set_viewport_size({"width": 1440, "height": 900})
                    page.once("dialog", lambda dialog: dialog.accept())
                    page.locator("#checkout-form").get_by_role("button").click()
                    expect(
                        page.get_by_role("link", name="Descargar PDF", exact=True)
                    ).to_be_visible()
                    invoice_route = page.url.removeprefix(address)
                    shot(
                        page,
                        "factura-detalle-desktop.png",
                        "EMPLOYEE",
                        "Factura TEST emitida por un cobro real sintético",
                    )
                    shot(
                        page,
                        "verifactu-desktop.png",
                        "EMPLOYEE",
                        "Alta TEST pendiente; ninguna aceptación inventada",
                        page.get_by_role("heading", name="Registro VERI*FACTU"),
                    )
                    page.goto(address + "/facturas/")
                    shot(page, "facturas-desktop.png", "EMPLOYEE", "Lista de documentos propios")
                    page.goto(address + "/clientes/")
                    shot(
                        page,
                        "clientes-desktop.png",
                        "EMPLOYEE",
                        "Ficha comercial sintética sin portal",
                    )
                    context.close()

                    context, page = login("demo_encargado")
                    page.goto(address + "/caja/")
                    shot(
                        page,
                        "arqueo-desktop.png",
                        "MANAGER",
                        "Controles de movimientos, arqueo y cierre",
                        page.get_by_role("heading", name="Arqueo y cierre"),
                    )
                    page.locator("[name=counted]").fill("62.10")
                    page.once("dialog", lambda dialog: dialog.accept())
                    page.get_by_role("button", name="Cerrar turno", exact=True).click()
                    expect(page.get_by_text("Cerrado", exact=True)).to_be_visible()
                    shot(
                        page,
                        "arqueo-cerrado-desktop.png",
                        "MANAGER",
                        "Turno cerrado realmente, sin diferencia",
                        page.get_by_text("Cerrado", exact=True),
                    )
                    page.goto(address + "/informes/")
                    shot(page, "informes-desktop.png", "MANAGER", "Informe de la venta sintética")
                    context.close()

                    context, page = login("demo_admin")
                    for route, filename, description in (
                        (
                            "/catalogo/",
                            "catalogo-desktop.png",
                            "Servicios y productos de demostración",
                        ),
                        (
                            "/catalogo/categorias/",
                            "categorias-desktop.png",
                            "Categorías, orden y visibilidad",
                        ),
                        (
                            "/empresa/?section=commercial",
                            "configuracion-desktop.png",
                            "Ajustes comerciales y logotipo",
                        ),
                        (
                            "/empresa/?section=fiscal",
                            "configuracion-fiscal-desktop.png",
                            "Identidad, zona horaria y series",
                        ),
                        (
                            "/empresa/?section=pos",
                            "configuracion-tpv-desktop.png",
                            "Preferencias visuales y operativas",
                        ),
                        ("/usuarios/", "usuarios-desktop.png", "Equipo y jerarquía"),
                        (
                            "/plano/configuracion/",
                            "configuracion-plano-desktop.png",
                            "Secciones y puestos configurables",
                        ),
                        (
                            "/caja/configuracion/",
                            "configuracion-cajas-desktop.png",
                            "Cajas configurables",
                        ),
                    ):
                        response = page.goto(address + route)
                        assert response.status == 200, route
                        shot(page, filename, "ADMIN", description)
                    context.close()

                    context, page = login("demo_superadmin")
                    for scope in ("TECHNICAL", "PII", "BACKUP", "UPDATE"):
                        page.goto(address + "/soporte/")
                        form = page.locator("form").filter(has=page.locator("[name=justification]"))
                        form.locator("[name=justification]").fill(
                            "Documentación de la DEMO sintética independiente"
                        )
                        form.locator("[name=scope]").select_option(scope)
                        form.locator("[name=approver_username]").fill("demo_admin")
                        form.locator("[name=password]").fill(users["demo_admin"]["Contrasena"])
                        form.locator("button").click()
                    page.goto(address + "/soporte/")
                    page.locator("form[action='/soporte/backup/'] button").click()
                    shot(
                        page,
                        "superadmin-dashboard.png",
                        "SUPERADMIN",
                        "Panel técnico real y métricas medidas",
                    )
                    shot(
                        page,
                        "backups-desktop.png",
                        "SUPERADMIN",
                        "Copias cifradas generadas realmente",
                        page.get_by_role("heading", name="Copias de seguridad"),
                    )
                    page.goto(address + "/soporte/")
                    page.get_by_role("button", name="Ejecutar diagnóstico", exact=True).click()
                    assert page.locator("body").inner_text().startswith("{")
                    shot(
                        page,
                        "diagnostico-desktop.png",
                        "SUPERADMIN",
                        "Respuesta JSON real del diagnóstico sin prueba AEAT",
                    )
                    for route, filename, description in (
                        (
                            "/soporte/terminales/",
                            "terminales-desktop.png",
                            "Terminal y preferencias",
                        ),
                        (
                            "/soporte/dispositivos/",
                            "impresoras-desktop.png",
                            "Formulario real de impresora; solo simulador en DEMO",
                        ),
                        (
                            "/soporte/actualizaciones/",
                            "actualizaciones-desktop.png",
                            "Comprobación de paquete; historial vacío real",
                        ),
                        (
                            "/soporte/fiscal/",
                            "certificado-desktop.png",
                            "TEST fijo, sin certificados en DEMO",
                        ),
                        (
                            "/soporte/restauracion/",
                            "restauracion-desktop.png",
                            "Preparación offline; no se ejecuta restauración",
                        ),
                        (
                            "/soporte/incidencias/",
                            "incidencias-desktop.png",
                            "Registro y clasificación sin datos personales",
                        ),
                    ):
                        response = page.goto(address + route)
                        assert response.status == 200, route
                        shot(page, filename, "SUPERADMIN", description)
                    page.goto(address + invoice_route)
                    shot(
                        page,
                        "cola-fiscal-desktop.png",
                        "SUPERADMIN",
                        "Consulta con PII autorizada, registroTEST pendiente",
                        page.get_by_role("heading", name="Registro VERI*FACTU"),
                    )
                    context.close()
                    browser.close()
                import sqlite3

                with sqlite3.connect(directory / "demo.sqlite3") as database:
                    assert (
                        database.execute(
                            "SELECT COUNT(*) FROM verifactu_fiscaltransmission"
                        ).fetchone()[0]
                        == 0
                    )
                manifest = {
                    "product_version": "0.1.0",
                    "date": "2026-11-15",
                    "source": "Chromium real + Waitress; independent temporary DEMO, not port8000",
                    "fiscal_transmissions": 0,
                    "credentials_included": False,
                    "images": records,
                }
                (output / "manifest.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            finally:
                if process.poll() is None:
                    with WindowsEvent(token, create=False) as signal:
                        signal.set()
                process.wait(timeout=30)
    return len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / "docs/screenshots"))
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--instance-dir")
    parser.add_argument("--port", type=int)
    parser.add_argument("--token")
    args = parser.parse_args()
    if args.serve:
        serve(Path(args.instance_dir), args.port, args.token)
    else:
        print(f"Capturas reales generadas: {capture(Path(args.output).resolve())}")
