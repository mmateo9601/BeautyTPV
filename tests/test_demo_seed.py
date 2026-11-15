"""DEMO preparation guard tests and behavior on pytest's isolated database."""

import json
import os
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from scripts import demo_seed


@pytest.fixture
def demo_marker(tmp_path, monkeypatch):
    root = tmp_path / "DEMO"
    root.mkdir()
    (root / "config.json").write_text(
        json.dumps({"kind": "BeautyTPV-DEMO", "version": 1}), encoding="utf-8"
    )
    database = root / "demo.sqlite3"
    database.touch()
    monkeypatch.setattr(
        demo_seed,
        "settings",
        SimpleNamespace(
            LOCAL_DEMO_ONLY=True,
            SETTINGS_MODULE="config.demo_settings",
            DATABASES={"default": {"NAME": str(database)}},
        ),
    )
    monkeypatch.setenv("BEAUTYTPV_DEMO_DIR", str(root))
    monkeypatch.setattr(
        demo_seed, "connection", SimpleNamespace(settings_dict={"NAME": str(database)})
    )
    return root


def test_seed_guard_accepts_exact_marked_database_without_accessing_orm(demo_marker):
    assert demo_seed.assert_demo_context() == demo_marker


@pytest.mark.parametrize(
    "failure", ["normal_settings", "wrong_marker", "wrong_database", "hardlink"]
)
def test_seed_guard_refuses_unsafe_context_before_writes(demo_marker, failure):
    if failure == "normal_settings":
        demo_seed.settings.SETTINGS_MODULE = "config.settings"
    elif failure == "wrong_marker":
        (demo_marker / "config.json").write_text("{}", encoding="utf-8")
    elif failure == "wrong_database":
        demo_seed.settings.DATABASES["default"]["NAME"] = str(
            demo_marker.parent / "principal.sqlite3"
        )
    elif failure == "hardlink":
        os.link(demo_marker / "demo.sqlite3", demo_marker / "another.sqlite3")
    with pytest.raises(ValidationError):
        demo_seed.prepare_demo()


@pytest.fixture
def isolated_seed(db, monkeypatch):
    # Test behavior in pytest's isolated transactional database. The actual
    # path/profile guard is exercised independently above without SQL.
    monkeypatch.setattr(demo_seed, "assert_demo_context", lambda: None)


def test_first_seed_creates_random_hashed_roles_and_only_synthetic_setup(isolated_seed):
    from apps.accounts.models import User
    from apps.audit.models import AuditEvent
    from apps.cash.models import CashRegister, CashSession
    from apps.catalog.models import CatalogItem
    from apps.core.models import CompanySettings, Terminal
    from apps.hardware.models import Printer
    from apps.layout.models import Station
    from apps.verifactu.models import FiscalTransmission

    credentials = demo_seed.prepare_demo()
    assert len(credentials) == 4
    assert len({row["password"] for row in credentials.values()}) == 4
    assert User.objects.count() == 4
    assert set(User.objects.values_list("role", flat=True)) == set(User.Role.values)
    for username, row in credentials.items():
        user = User.objects.get(username=username)
        assert user.check_password(row["password"]) and user.check_pin(row["pin"])
        assert row["password"] != user.password and row["pin"] != user.pin_hash
    company = CompanySettings.load()
    assert company.name == "Centro DEMO" and company.fiscal_mode == "TEST"
    assert company.quick_sale_enabled
    assert set(Station.objects.values_list("code", flat=True)) == {"A1", "A2", "A3", "B1"}
    assert CatalogItem.objects.filter(kind="PRODUCT", tax_rate="10").exists()
    assert CatalogItem.objects.filter(kind="SERVICE").count() == 2
    assert CashRegister.objects.get(name="Caja DEMO").terminal is None
    assert Terminal.objects.get(code="demo").default_register.name == "Caja DEMO"
    assert Printer.objects.get().connection_type == "SIMULATOR"
    assert Printer.objects.get().terminal is None
    assert not CashSession.objects.exists()
    assert not FiscalTransmission.objects.exists()
    assert AuditEvent.objects.filter(action="demo.initialized").count() == 1


def test_restart_does_not_reseed_credentials_or_change_demo_user_edits(isolated_seed):
    from apps.accounts.models import User
    from apps.catalog.models import CatalogItem
    from apps.core.models import CompanySettings

    credentials = demo_seed.prepare_demo()
    before = dict(User.objects.values_list("username", "password"))
    company = CompanySettings.load()
    company.trade_name = "Ajuste de prueba persistente"
    company.save()
    assert demo_seed.prepare_demo() is None
    assert dict(User.objects.values_list("username", "password")) == before
    assert CompanySettings.load().trade_name == "Ajuste de prueba persistente"
    assert CatalogItem.objects.count() == 3
    assert User.objects.get(username="demo_empleado").check_password(
        credentials["demo_empleado"]["password"]
    )


def test_explicit_recovery_rotates_only_demo_users_and_revokes_support(isolated_seed):
    from apps.accounts.models import User
    from apps.support.models import SupportSession

    before = demo_seed.prepare_demo()
    outside = User.objects.create_user(
        username="additional-local-user", password="Random role 8964!"
    )
    root = User.objects.get(username="demo_superadmin")
    approver = User.objects.get(username="demo_admin")
    grant = SupportSession.objects.create(
        actor=root,
        approved_by=approver,
        scope="PII",
        justification="Revisión de datos sintéticos",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    auth_version = root.auth_version
    after = demo_seed.prepare_demo(rotate_users=True)
    assert all(before[name]["password"] != after[name]["password"] for name in before)
    root.refresh_from_db()
    grant.refresh_from_db()
    outside.refresh_from_db()
    assert root.auth_version == auth_version + 1 and grant.revoked_at is not None
    assert outside.check_password("Random role 8964!")


def test_seed_never_silently_reclassifies_existing_fiscal_configuration(isolated_seed):
    from apps.core.models import CompanySettings

    company = CompanySettings.load()
    company.fiscal_mode = "PRODUCTION"
    company.save()
    with pytest.raises(ValidationError):
        demo_seed.prepare_demo()
    assert CompanySettings.load().fiscal_mode == "PRODUCTION"
