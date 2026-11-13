"""Superadmin forms against a real isolated server/SQLite. No external AEAT or device IO."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from playwright.sync_api import expect
from test_browser import ROOT, centre_server  # noqa: F401


@pytest.fixture
def configured_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("BEAUTYTPV_BACKUP_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("BEAUTYTPV_BACKUP_DIR", str(tmp_path / "encrypted-backups"))


@pytest.fixture
def technical_server(configured_environment, centre_server):  # noqa: F811
    return centre_server


def database_value(database, expression):
    code = (
        "import json; from apps.core.models import Terminal; from apps.hardware.models import Printer; from apps.support.models import TechnicalSettings,BackupRun; print(json.dumps("
        + expression
        + "))"
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


def login_technician(page, address, database):
    result = subprocess.run(
        [
            sys.executable,
            "manage.py",
            "shell",
            "-c",
            "from apps.accounts.models import User; User.objects.filter(username='browser').update(role='SUPERADMIN')",
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


def authorize(page, address, scope):
    page.goto(address + "/soporte/")
    form = page.locator("form").filter(has=page.locator("[name=justification]"))
    form.locator("[name=justification]").fill("Auditoria operativa de formularios reales")
    form.locator("[name=scope]").select_option(scope)
    form.locator("[name=approver_username]").fill("browser")
    form.locator("[name=password]").fill("Browser-Password-194!")
    form.locator("button").click()
    expect(page).to_have_url(address + "/soporte/")


def test_superadmin_terminal_printer_and_fiscal_configuration_forms(page, technical_server):
    address, database = technical_server
    login_technician(page, address, database)
    authorize(page, address, "TECHNICAL")
    page.goto(address + "/soporte/terminales/")
    page.locator("[name=code]").fill("audit-ui")
    page.locator("[name=name]").fill("Terminal auditoria UI")
    token = "synthetic-terminal-token-" * 3
    page.locator("[name=bridge_token]").fill(token)
    page.locator("form").filter(has=page.locator("[name=code]")).locator("button").click()
    terminal = database_value(
        database, "dict(Terminal.objects.get(code='audit-ui').__dict__,_state=None)"
    )
    assert terminal["active"] and terminal["bridge_token_hash"] != token
    assert token not in page.locator("body").inner_text()
    page.goto(address + "/soporte/dispositivos/")
    page.locator("[name=name]").fill("Simulador UI identificado")
    page.locator("[name=connection_type]").select_option("SIMULATOR")
    page.locator("[name=terminal]").select_option(str(terminal["id"]))
    page.locator("form").filter(has=page.locator("[name=connection_type]")).locator(
        "button"
    ).click()
    assert (
        database_value(
            database, "Printer.objects.get(name='Simulador UI identificado').terminal_id"
        )
        == terminal["id"]
    )
    page.goto(address + "/soporte/fiscal/")
    page.locator("[name=fiscal_environment]").select_option("TEST")
    page.locator("form").filter(has=page.locator("[name=fiscal_environment]")).locator(
        "button"
    ).click()
    assert database_value(database, "TechnicalSettings.load().fiscal_environment") == "TEST"
    # This tests reference/config wiring; PEM/key validity has separate cryptographic unit tests.
    page.goto(address + "/soporte/")
    evidence = Path(ROOT) / "docs/evidence/audit-superadmin.png"
    page.screenshot(path=str(evidence), full_page=True)


def test_superadmin_creates_encrypted_backup_and_prepares_offline_restore(page, technical_server):
    address, database = technical_server
    login_technician(page, address, database)
    authorize(page, address, "BACKUP")
    page.locator("form[action='/soporte/backup/'] button").click()
    assert database_value(database, "BackupRun.objects.filter(status='COMPLETE').count()") == 1
    page.goto(address + "/soporte/restauracion/")
    page.locator("[name=backup]").select_option(index=1)
    page.locator("[name=confirmation]").fill("PREPARAR RESTAURACION")
    page.locator("form").filter(has=page.locator("[name=confirmation]")).locator("button").click()
    expect(page.get_by_text("Copia verificada:", exact=False)).to_be_visible()
    assert database_value(database, "TechnicalSettings.load().maintenance") is True
    page.goto(address + "/tpv/")
    with page.expect_response(
        lambda response: "/tpv/puestos/" in response.url and response.request.method == "POST"
    ) as blocked:
        page.get_by_role("button", name="Puesto A1, libre", exact=True).click()
    assert blocked.value.status == 503
