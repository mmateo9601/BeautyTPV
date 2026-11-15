"""Synthetic data for an explicitly validated, isolated Windows DEMO database.

The caller migrates/bootstrap the database first and delivers returned random
credentials through its private local store. This module never prints secrets.
"""

import json
import os
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

DEMO_USERS = {
    "demo_superadmin": ("SUPERADMIN", "Superadmin DEMO"),
    "demo_admin": ("ADMIN", "Administrador DEMO"),
    "demo_encargado": ("MANAGER", "Encargado DEMO"),
    "demo_empleado": ("EMPLOYEE", "Empleado DEMO"),
}


def assert_demo_context():
    """Refuse normal settings, linked databases and unmarked directories before ORM."""
    raw = os.environ.get("BEAUTYTPV_DEMO_DIR", "")
    if (
        not raw
        or not getattr(settings, "LOCAL_DEMO_ONLY", False)
        or settings.SETTINGS_MODULE != "config.demo_settings"
    ):
        raise ValidationError("La semilla solo puede ejecutarse en el perfil DEMO aislado.")
    directory = Path(raw)
    if not directory.is_absolute() or directory.is_symlink() or directory.is_junction():
        raise ValidationError("Directorio DEMO no válido o enlazado.")
    directory = directory.resolve()
    marker = directory / "config.json"
    try:
        if marker.is_symlink():
            raise ValueError
        config = json.loads(marker.read_text(encoding="utf-8"))
        if config.get("kind") != "BeautyTPV-DEMO" or config.get("version") != 1:
            raise ValueError
    except (OSError, ValueError, AttributeError):
        raise ValidationError(
            "Falta una configuración DEMO válida; no se modificó la base."
        ) from None
    expected = directory / "demo.sqlite3"
    for filename in (settings.DATABASES["default"]["NAME"], connection.settings_dict["NAME"]):
        actual = Path(filename)
        if not actual.is_absolute() or actual.is_symlink() or actual.resolve() != expected:
            raise ValidationError("La base configurada no es la SQLite DEMO independiente.")
    if not expected.is_file() or expected.stat().st_nlink != 1:
        raise ValidationError("La base DEMO debe existir, ser local y no tener enlaces físicos.")
    return directory


def _validate_fiscal_state():
    from apps.billing.models import Invoice
    from apps.core.models import CompanySettings
    from apps.support.models import TechnicalSettings

    company = CompanySettings.load()
    technical = TechnicalSettings.load()
    if (
        company.fiscal_mode != "TEST"
        or technical.fiscal_environment != "TEST"
        or technical.certificate_path
        or technical.private_key_path
        or Invoice.objects.exclude(fiscal_mode="TEST").exists()
        or getattr(settings, "FISCAL_PRODUCTION_APPROVED", False)
    ):
        raise ValidationError("La DEMO exige TEST sin certificados ni documentos productivos.")
    return company, technical


def _random_credentials(user):
    password = secrets.token_urlsafe(18)
    pin = f"{secrets.randbelow(1_000_000):06d}"
    validate_password(password, user)
    user.set_password(password)
    user.set_pin(pin)
    return {"password": password, "pin": pin, "role": user.role}


def _rotate_demo_users():
    from apps.accounts.models import LoginThrottle, User
    from apps.audit.services import record
    from apps.support.models import SupportSession

    credentials = {}
    for username, (role, name) in DEMO_USERS.items():
        user, created = User.objects.get_or_create(username=username)
        user.role = role
        user.first_name = name
        user.is_active = True
        user.is_staff = role in ("ADMIN", "SUPERADMIN")
        user.is_superuser = role == "SUPERADMIN"
        credentials[username] = _random_credentials(user)
        if not created:
            user.auth_version += 1
        user.full_clean()
        user.save()
        SupportSession.objects.filter(
            Q(actor=user) | Q(approved_by=user), revoked_at__isnull=True
        ).update(revoked_at=timezone.now())
    # This profile is an isolated demo; explicit credential recovery also clears
    # temporary local sign-in throttles. Never call against a real installation.
    LoginThrottle.objects.all().delete()
    record(None, "demo.credentials_configured", metadata={"count": len(credentials)})
    return credentials


def prepare_demo(rotate_users=False):
    """Create data once; rotate only explicit demo accounts on requested recovery.

    Returns username -> {password, pin, role} only on creation/recovery, otherwise
    None. Caller must write this privately before claiming setup succeeded.
    """
    assert_demo_context()
    from apps.accounts.models import User
    from apps.audit.models import AuditEvent
    from apps.audit.services import record
    from apps.cash.models import CashRegister
    from apps.catalog.models import CatalogItem, Category
    from apps.core.models import Terminal
    from apps.customers.models import Customer
    from apps.hardware.models import Printer
    from apps.layout.models import Section, Station

    with transaction.atomic():
        company, technical = _validate_fiscal_state()
        if AuditEvent.objects.filter(action="demo.initialized").exists():
            return _rotate_demo_users() if rotate_users else None
        if User.objects.exists() or company.tax_id not in ("", "89890001K"):
            raise ValidationError(
                "La base contiene usuarios o una identidad previa sin marcador DEMO. "
                "No se sobrescriben; revise la preparación."
            )
        company.name = "Centro DEMO"
        company.trade_name = "Salón DEMO"
        company.tax_id = "89890001K"
        company.address = "Calle sintética 1, entorno de demostración"
        company.currency = "EUR"
        company.producer_name = "Productor sintético DEMO"
        company.producer_tax_id = "89890001K"
        company.fiscal_mode = "TEST"
        company.quick_sale_enabled = True
        company.ticket_footer = "DEMO: datos sintéticos, sin validez fiscal productiva"
        company.full_clean()
        company.save()
        technical.fiscal_environment = "TEST"
        technical.certificate_path = ""
        technical.private_key_path = ""
        technical.maintenance = False
        technical.save()
        for order, (name, count) in enumerate((("A", 3), ("B", 1))):
            section, _ = Section.objects.get_or_create(name=name, defaults={"sort_order": order})
            for index in range(1, count + 1):
                code = f"{name}{index}"
                Station.objects.get_or_create(
                    code=code,
                    defaults={"name": f"Puesto {code}", "section": section, "sort_order": index},
                )
        services, _ = Category.objects.get_or_create(
            name="Servicios DEMO", defaults={"sort_order": 0}
        )
        products, _ = Category.objects.get_or_create(
            name="Productos DEMO", defaults={"sort_order": 1}
        )
        for name, kind, price, rate, category in (
            ("Manicura DEMO", "SERVICE", "12.10", "21", services),
            ("Tratamiento DEMO", "SERVICE", "30.25", "21", services),
            ("Crema DEMO", "PRODUCT", "11.00", "10", products),
        ):
            CatalogItem.objects.get_or_create(
                name=name,
                defaults={"kind": kind, "price": price, "tax_rate": rate, "category": category},
            )
        Customer.objects.get_or_create(
            name="Cliente DEMO",
            defaults={"legal_basis": "Datos sintéticos de demostración, sin persona real"},
        )
        register, _ = CashRegister.objects.get_or_create(name="Caja DEMO")
        Terminal.objects.get_or_create(
            code="demo", defaults={"name": "Terminal DEMO", "default_register": register}
        )
        Printer.objects.get_or_create(
            name="Impresora simulada DEMO",
            defaults={"connection_type": "SIMULATOR", "enabled": True, "terminal": None},
        )
        credentials = _rotate_demo_users()
        record(None, "demo.initialized", metadata={"count": len(credentials)})
        return credentials
