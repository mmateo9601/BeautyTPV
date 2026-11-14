"""Independent consolidation checks: real HTTP boundaries, services and SQLite state.

No AEAT acceptance or physical-device result is inferred from these tests.
"""

import io

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection, transaction
from django.test import Client
from django.urls import reverse
from PIL import Image
from test_audit_matrix import audit_centre, signed_client  # noqa: F401

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.core.models import CompanySettings
from apps.pos.services import add_line


def png_upload():
    stream = io.BytesIO()
    Image.new("RGB", (900, 400), "#123456").save(stream, "PNG")
    return SimpleUploadedFile("brand.png", stream.getvalue(), content_type="image/png")


@pytest.mark.parametrize(
    "payload",
    [
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b"<html><img src=x onerror=alert(1)></html>",
        b"\x89PNG\r\n\x1a\nnot-an-image",
        b"x" * (2 * 1024 * 1024 + 1),
    ],
)
def test_logo_rejects_active_malformed_and_oversize_content_atomically(audit_centre, payload):  # noqa: F811
    from apps.core.services import save_company_settings

    before = CompanySettings.load()
    with pytest.raises(ValidationError):
        save_company_settings(
            audit_centre["users"]["ADMIN"],
            {"trade_name": "Must not persist"},
            logo=SimpleUploadedFile("logo.png", payload, content_type="image/png"),
        )
    after = CompanySettings.load()
    assert after.trade_name == before.trade_name and bytes(after.logo_data) == bytes(
        before.logo_data
    )


def test_valid_logo_is_canonical_private_png_and_removal_is_audited(audit_centre):  # noqa: F811
    from apps.core.services import save_company_settings

    admin = signed_client(audit_centre, "ADMIN")
    response = admin.post(reverse("core:logo_save"), {"logo": png_upload()})
    assert response.status_code == 302
    image = CompanySettings.load().logo_data
    assert bytes(image).startswith(b"\x89PNG\r\n\x1a\n")
    with Image.open(io.BytesIO(bytes(image))) as decoded:
        assert decoded.format == "PNG" and max(decoded.size) <= 600
    employee = signed_client(audit_centre, "EMPLOYEE")
    logo = employee.get(reverse("core:logo"))
    assert logo.status_code == 200 and logo.content == bytes(image)
    assert logo.headers["Content-Type"] == "image/png"
    assert logo.headers["X-Content-Type-Options"] == "nosniff"
    assert "private" in logo.headers["Cache-Control"]
    assert Client().get(reverse("core:logo")).status_code in {302, 403}
    assert employee.post(reverse("core:logo_save"), {"remove_logo": "on"}).status_code == 403
    save_company_settings(audit_centre["users"]["ADMIN"], {}, remove_logo=True)
    assert employee.get(reverse("core:logo")).status_code == 404
    assert AuditEvent.objects.filter(action="company.settings").count() >= 2


def test_commercial_form_cannot_smuggle_fiscal_identity_or_production(audit_centre):  # noqa: F811
    company = CompanySettings.load()
    previous = (company.tax_id, company.installation_number, company.fiscal_mode)
    client = signed_client(audit_centre, "ADMIN")
    response = client.post(
        reverse("core:settings") + "?section=commercial",
        {
            "trade_name": "Salon QA",
            "commercial_address": "Calle de prueba",
            "email": "salon@example.test",
            "phone": "900000000",
            "ticket_footer": "Gracias por su visita",
            "tax_id": "12345678Z",
            "installation_number": "untrusted",
            "fiscal_mode": "PRODUCTION",
        },
    )
    assert response.status_code == 302
    company.refresh_from_db()
    assert company.trade_name == "Salon QA" and company.email == "salon@example.test"
    assert (company.tax_id, company.installation_number, company.fiscal_mode) == previous
    assert client.get(reverse("core:settings") + "?section=unknown").status_code == 400


def test_company_service_uses_persisted_role_and_rejects_unsupported_currency(audit_centre):  # noqa: F811
    from apps.core.services import save_company_settings

    actor = audit_centre["users"]["ADMIN"]
    with pytest.raises(ValidationError):
        save_company_settings(actor, {"currency": "USD"})
    assert CompanySettings.load().currency == "EUR"
    User.objects.filter(pk=actor.pk).update(role="EMPLOYEE")
    with pytest.raises(PermissionDenied):
        save_company_settings(actor, {"trade_name": "Escalated"})
    assert CompanySettings.load().trade_name != "Escalated"


def test_hidden_category_cannot_be_added_by_direct_post_or_stale_item(audit_centre):  # noqa: F811
    category = audit_centre["category"]
    category.visible_in_pos = False
    category.save()
    ticket = audit_centre["ticket"]
    item = audit_centre["item"]
    count = ticket.lines.count()
    with pytest.raises(ValidationError):
        add_line(ticket, item, audit_centre["employee"])
    response = signed_client(audit_centre, "EMPLOYEE").post(
        reverse("pos:add_line", args=[ticket.pk]), {"item_id": item.pk, "quantity": "1"}
    )
    assert response.status_code == 400 and ticket.lines.count() == count


def test_incident_cannot_cross_operational_scope_or_overwrite_concurrent_action(audit_centre):  # noqa: F811
    from apps.support.incidents import add_action, create_incident, visible_incidents
    from apps.support.models import IncidentAction

    manager = audit_centre["users"]["MANAGER"]
    technical = create_incident(
        audit_centre["users"]["SUPERADMIN"],
        title="Impresora sin respuesta",
        description="Revisar cable de dispositivo",
        category="HARDWARE",
    )
    assert not visible_incidents(manager).filter(pk=technical.pk).exists()
    with pytest.raises(PermissionDenied):
        add_action(
            manager,
            technical,
            note="Acceso no permitido",
            status="RESOLVED",
            category="OPERATIONAL",
            severity="LOW",
            version=0,
        )
    incident = create_incident(
        manager, title="Puesto pendiente", description="Revisar puesto libre"
    )
    with pytest.raises(PermissionDenied):
        add_action(
            manager,
            incident,
            note="Escalar sin permiso",
            status="IN_PROGRESS",
            category="SYSTEM",
            severity="HIGH",
            version=0,
        )
    resolved = add_action(
        manager,
        incident,
        note="Puesto revisado",
        status="RESOLVED",
        category="OPERATIONAL",
        severity="LOW",
        version=0,
    )
    with pytest.raises(ValidationError):
        add_action(
            manager,
            incident,
            note="Escritura obsoleta",
            status="OPEN",
            category="OPERATIONAL",
            severity="LOW",
            version=0,
        )
    assert IncidentAction.objects.filter(incident=incident).count() == 1
    assert resolved.status == "RESOLVED" and resolved.resolved_at is not None
    reopened = add_action(
        manager,
        resolved,
        note="Nueva comprobacion necesaria",
        status="OPEN",
        category="OPERATIONAL",
        severity="MEDIUM",
        version=resolved.version,
    )
    assert reopened.resolved_at is None and reopened.actions.count() == 2


@pytest.mark.parametrize("statement", ["UPDATE", "DELETE", "REPLACE"])
def test_incident_action_history_is_guarded_even_in_raw_sql(audit_centre, statement):  # noqa: F811
    from apps.support.incidents import add_action, create_incident

    actor = audit_centre["users"]["MANAGER"]
    incident = create_incident(actor, title="Comprobacion", description="Revision operativa")
    add_action(
        actor,
        incident,
        note="Revision completada",
        status="RESOLVED",
        category="OPERATIONAL",
        severity="LOW",
        version=0,
    )
    action = incident.actions.get()
    table = "support_incidentaction"
    statements = {
        "UPDATE": f"UPDATE {table} SET note='changed' WHERE id=%s",
        "DELETE": f"DELETE FROM {table} WHERE id=%s",
        "REPLACE": f"INSERT OR REPLACE INTO {table} SELECT * FROM {table} WHERE id=%s",
    }
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(statements[statement], [action.pk])
    action.refresh_from_db()
    assert action.note == "Revision completada"


def test_http_revocation_invalidates_all_existing_logins_without_changing_credentials(audit_centre):  # noqa: F811
    actor = audit_centre["users"]["EMPLOYEE"]
    credentials = (actor.password, actor.pin_hash)
    first = signed_client(audit_centre, "EMPLOYEE")
    second = signed_client(audit_centre, "EMPLOYEE")
    url = reverse("team:revoke_sessions", args=[actor.pk])
    assert (
        signed_client(audit_centre, "MANAGER")
        .post(url, {"confirmation": "REVOCAR SESIONES"})
        .status_code
        == 403
    )
    admin = signed_client(audit_centre, "ADMIN")
    assert admin.post(url, {"confirmation": "wrong"}).status_code == 400
    assert first.get(reverse("pos:floor")).status_code == 200
    assert admin.post(url, {"confirmation": "REVOCAR SESIONES"}).status_code == 302
    actor.refresh_from_db()
    assert (actor.password, actor.pin_hash) == credentials
    for client in (first, second):
        assert client.get(reverse("pos:floor")).status_code in {302, 403}
    assert AuditEvent.objects.filter(
        action="user.sessions_revoked", target=f"accounts.User:{actor.pk}"
    ).exists()


def test_register_and_station_configuration_cannot_invalidate_live_operations(audit_centre):  # noqa: F811
    from apps.cash.services import save_register
    from apps.layout.models import Section
    from apps.layout.services import save_station

    admin = audit_centre["users"]["ADMIN"]
    register = audit_centre["cash_session"].register
    register.active = False
    with pytest.raises(ValidationError):
        save_register(admin, register)
    register.refresh_from_db()
    assert register.active
    register.terminal = audit_centre["terminal"]
    with pytest.raises(ValidationError):
        save_register(admin, register)
    register.refresh_from_db()
    assert register.terminal_id is None
    station = audit_centre["station"]
    station.active = False
    with pytest.raises(ValidationError):
        save_station(admin, station)
    station.refresh_from_db()
    assert station.active
    original_section = station.section_id
    station.section = Section.objects.create(name="Otra zona")
    with pytest.raises(ValidationError):
        save_station(admin, station)
    station.refresh_from_db()
    assert station.section_id == original_section
    assert audit_centre["ticket"].lines.count() == 1


@pytest.mark.parametrize("entity", ["category", "item", "section", "station", "register"])
def test_administrative_entity_services_reject_manager_without_http(entity, audit_centre):  # noqa: F811
    from apps.cash.services import save_register
    from apps.catalog.services import save_catalog_item, save_category
    from apps.layout.services import save_section, save_station

    services = {
        "category": save_category,
        "item": save_catalog_item,
        "section": save_section,
        "station": save_station,
        "register": save_register,
    }
    obj = audit_centre["register"] if entity == "register" else audit_centre[entity]
    with pytest.raises(PermissionDenied):
        services[entity](audit_centre["users"]["MANAGER"], obj)


def test_register_service_checks_terminal_activity_from_database(audit_centre):  # noqa: F811
    from apps.cash.models import CashRegister
    from apps.cash.services import save_register
    from apps.core.models import Terminal

    terminal = audit_centre["terminal"]
    register = CashRegister(name="Caja terminal obsoleta", terminal=terminal)
    Terminal.objects.filter(pk=terminal.pk).update(active=False)
    with pytest.raises(ValidationError):
        save_register(audit_centre["users"]["ADMIN"], register)
    assert not CashRegister.objects.filter(name=register.name).exists()


def test_superadmin_operational_inheritance_does_not_bypass_incident_support_controls(audit_centre):  # noqa: F811
    from django.utils import timezone

    urls = [
        reverse("support:incidents"),
        reverse("support:incident_detail", args=[audit_centre["incident"].pk]),
    ]
    unelevated = signed_client(audit_centre, "SUPERADMIN", elevated=False)
    for url in urls:
        assert unelevated.get(url).status_code == 403
    grant = audit_centre["authorizations"]["TECHNICAL"]
    grant.revoked_at = timezone.now()
    grant.save()
    elevated = signed_client(audit_centre, "SUPERADMIN")
    for url in urls:
        assert elevated.get(url).status_code == 403
    for url in urls:
        assert signed_client(audit_centre, "MANAGER").get(url).status_code == 200
