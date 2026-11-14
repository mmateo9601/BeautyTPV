"""Consolidation operations: actual services, HTTP, persisted history and backup IO."""

import sqlite3
from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.core.models import Terminal
from apps.support.incidents import add_action, create_incident, incident_text, visible_incidents
from apps.support.models import (
    BackupRun,
    Incident,
    IncidentAction,
    SupportSession,
    TechnicalSettings,
)
from apps.support.services import diagnostics, save_terminal

pytestmark = pytest.mark.django_db


@pytest.fixture
def operators():
    users = {
        role: User.objects.create_user(username="consolidation-" + role, role=role)
        for role in User.Role.values
    }
    SupportSession.objects.create(
        actor=users["SUPERADMIN"],
        approved_by=users["ADMIN"],
        scope="TECHNICAL",
        justification="Configuracion local",
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    return users


def client_for(user):
    client = Client()
    client.force_login(user)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    return client


def act(actor, incident, **changes):
    values = dict(
        note="Se reviso el procedimiento",
        status=incident.status,
        category=incident.category,
        severity=incident.severity,
        version=incident.version,
    )
    values.update(changes)
    return add_action(actor, incident, **values)


def test_incident_complete_service_lifecycle_and_retained_history(operators):
    manager = operators["MANAGER"]
    incident = create_incident(
        manager, title="Revisar puesto", description="El puesto no esta disponible"
    )
    incident = act(manager, incident, status="IN_PROGRESS", severity="HIGH")
    incident = act(manager, incident, status="RESOLVED", note="Puesto disponible tras comprobacion")
    resolved = incident.resolved_at
    assert resolved and incident.actions.count() == 2
    incident = act(manager, incident, status="OPEN", note="Se reproduce el problema")
    assert incident.resolved_at is None and incident.version == 3
    assert list(incident.actions.values_list("previous_status", "new_status")) == [
        ("OPEN", "IN_PROGRESS"),
        ("IN_PROGRESS", "RESOLVED"),
        ("RESOLVED", "OPEN"),
    ]
    assert AuditEvent.objects.filter(action="incident.action").count() == 3
    assert not any("Puesto disponible" in str(event.metadata) for event in AuditEvent.objects.all())


def test_incident_stale_form_and_invalid_transition_do_not_add_history(operators):
    manager = operators["MANAGER"]
    incident = create_incident(manager, title="Procedimiento", description="Revisar operativa")
    incident = act(manager, incident, status="RESOLVED")
    with pytest.raises(ValidationError, match="Transicion"):
        act(manager, incident, status="IN_PROGRESS")
    with pytest.raises(ValidationError, match="Otra persona"):
        act(manager, incident, version=0, status="OPEN")
    assert incident.actions.count() == 1


@pytest.mark.parametrize(
    "value",
    [
        "persona@example.com",
        "PIN: 123456",
        "Bearer any-secret",
        "<soap:Envelope>datos</soap:Envelope>",
        "89890001K",
        "4111111111111111",
        "log\x1bcomando",
    ],
)
def test_incident_text_rejects_common_sensitive_payloads(value):
    with pytest.raises(ValidationError):
        incident_text(value, 1000)


def test_incident_employee_denied_and_technical_scope_required(operators):
    with pytest.raises(PermissionDenied):
        create_incident(operators["EMPLOYEE"], title="Problema", description="Revisar")
    tech = create_incident(
        operators["SUPERADMIN"],
        title="Dispositivo no conectado",
        description="Revisar cableado",
        category="HARDWARE",
    )
    assert not visible_incidents(operators["MANAGER"]).filter(pk=tech.pk).exists()
    with pytest.raises(PermissionDenied):
        act(operators["ADMIN"], tech)
    SupportSession.objects.all().update(revoked_at=timezone.now())
    with pytest.raises(PermissionDenied):
        visible_incidents(operators["SUPERADMIN"])


def test_incident_http_creation_classification_resolution_and_search(operators):
    manager = operators["MANAGER"]
    client = client_for(manager)
    assert client.get(reverse("support:incidents")).status_code == 200
    payload = {
        "title": "Reposicion material",
        "description": "Preparar puesto antes del turno",
        "category": "OPERATIONAL",
        "severity": "HIGH",
    }
    assert client.post(reverse("support:incidents"), payload).status_code == 302
    incident = Incident.objects.get(title="Reposicion material")
    page = client.get(
        reverse("support:incidents"), {"q": "Reposicion", "status": "OPEN", "severity": "HIGH"}
    )
    assert list(page.context["incidents"]) == [incident]
    page = client.get(reverse("support:incident_detail", args=[incident.pk]))
    assert page.status_code == 200 and page.context["form"].initial["version"] == 0
    assert (
        client.post(
            reverse("support:incident_detail", args=[incident.pk]),
            dict(
                note="Material preparado",
                status="RESOLVED",
                category="OPERATIONAL",
                severity="MEDIUM",
                version=0,
            ),
        ).status_code
        == 302
    )
    incident.refresh_from_db()
    assert incident.status == "RESOLVED" and incident.actions.get().new_severity == "MEDIUM"
    assert client_for(operators["EMPLOYEE"]).get(reverse("support:incidents")).status_code == 403


def test_incident_sql_history_update_delete_and_replace_blocked(operators):
    incident = create_incident(
        operators["MANAGER"], title="Operativa", description="Revisar protocolo"
    )
    incident = act(operators["MANAGER"], incident)
    action = incident.actions.get()
    with pytest.raises(ValidationError):
        action.delete()
    statements = [
        ("UPDATE support_incidentaction SET note='alterada' WHERE id=%s", [action.pk]),
        ("DELETE FROM support_incidentaction WHERE id=%s", [action.pk]),
        (
            "INSERT OR REPLACE INTO support_incidentaction SELECT * FROM support_incidentaction WHERE id=%s",
            [action.pk],
        ),
        ("DELETE FROM support_incident WHERE id=%s", [incident.pk]),
    ]
    for sql, params in statements:
        with pytest.raises(Exception), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql, params)
    assert IncidentAction.objects.get(pk=action.pk).note == "Se reviso el procedimiento"


def test_session_revoke_http_keeps_credentials_and_revokes_existing_login(operators):
    employee = operators["EMPLOYEE"]
    employee.set_pin("839201")
    employee.save()
    old_pin = employee.pin_hash
    old_client = client_for(employee)
    admin = client_for(operators["ADMIN"])
    url = reverse("team:revoke_sessions", args=[employee.pk])
    assert admin.get(url).status_code == 405
    assert admin.post(url, {}).status_code == 400
    assert admin.post(url, {"confirmation": "REVOCAR SESIONES"}).status_code == 302
    employee.refresh_from_db()
    assert employee.pin_hash == old_pin and employee.auth_version == 1
    assert old_client.get("/tpv/").status_code == 403
    assert (
        client_for(operators["EMPLOYEE"])
        .post(url, {"confirmation": "REVOCAR SESIONES"})
        .status_code
        == 403
    )


def test_terminal_and_user_filters_and_service_authorization(operators):
    terminal = save_terminal(
        operators["SUPERADMIN"], Terminal(code="salon-norte", name="Terminal norte")
    )
    with pytest.raises(PermissionDenied):
        save_terminal(operators["ADMIN"], Terminal(code="no", name="No autorizada"))
    client = client_for(operators["SUPERADMIN"])
    result = client.get(reverse("support:terminals"), {"q": "norte", "active": "1"})
    assert list(result.context["terminals"]) == [terminal]
    result = client_for(operators["ADMIN"]).get(
        reverse("team:index"), {"q": "EMPLOYEE", "role": "EMPLOYEE", "state": "active"}
    )
    assert list(result.context["users"]) == [operators["EMPLOYEE"]]


def test_diagnostics_reports_installed_dependency_versions(operators):
    import django

    result = diagnostics()
    assert result["django_version"] == django.get_version()
    assert result["dependencies"]["Django"] == django.get_version()
    assert result["python_version"] and result["integrity"] == "ok"


def test_backup_verification_does_not_prepare_maintenance(
    operators, settings, monkeypatch, tmp_path
):
    from apps.support.operations import create_backup

    key = Fernet.generate_key()
    monkeypatch.setenv("BEAUTYTPV_BACKUP_KEY", key.decode())
    monkeypatch.setenv("BEAUTYTPV_BACKUP_DIR", str(tmp_path))
    db = tmp_path / "synthetic.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE example(id INTEGER)")
        conn.execute("CREATE TABLE django_migrations(app TEXT,name TEXT)")
        conn.execute("INSERT INTO example VALUES(1)")
    archive = tmp_path / "verification.btpv"
    _, digest = create_backup(db, archive, key)
    run = BackupRun.objects.create(filename=archive.name, sha256=digest)
    SupportSession.objects.create(
        actor=operators["SUPERADMIN"],
        approved_by=operators["ADMIN"],
        scope="BACKUP",
        justification="Verificar copia",
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    client = client_for(operators["SUPERADMIN"])
    assert client.post(reverse("support:backup_verify", args=[run.pk])).status_code == 302
    assert not TechnicalSettings.load().maintenance
    assert AuditEvent.objects.filter(action="backup.verified").exists()
    archive.write_bytes(b"damaged")
    assert client.post(reverse("support:backup_verify", args=[run.pk])).status_code == 302
    assert AuditEvent.objects.filter(action="backup.verification_failed").exists()
    assert not TechnicalSettings.load().maintenance
