from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts.middleware import SupportPIIMiddleware
from apps.accounts.models import User
from apps.accounts.permissions import require_elevated, require_role
from apps.accounts.services import update_user

pytestmark = pytest.mark.django_db


def test_pin_reset_revokes_existing_browser_session(client):
    operator = User.objects.create_user(username="operator-reset")
    operator.set_pin("481926")
    operator.save()
    owner = User.objects.create_user(username="owner-reset", role="SUPERADMIN")
    client.force_login(operator)
    update_user(owner, operator, pin="592037")
    assert client.get("/tpv/").status_code == 403


def test_role_change_revokes_existing_elevated_session(client):
    user = User.objects.create_user(
        username="promoted", role="EMPLOYEE", password="Some!Passphrase947"
    )
    owner = User.objects.create_user(username="owner-promote", role="SUPERADMIN")
    client.force_login(user)
    session = client.session
    session["elevated_until"] = (timezone.now() + timedelta(minutes=10)).timestamp()
    session.save()
    update_user(owner, user, role="ADMIN")
    assert client.get("/empresa/").status_code == 403


def test_stale_target_does_not_allow_admin_to_edit_new_superadmin():
    actor = User.objects.create_user(username="stale-admin", role="ADMIN")
    target = User.objects.create_user(username="stale-target", role="EMPLOYEE")
    User.objects.filter(pk=target.pk).update(role="SUPERADMIN")
    with pytest.raises(PermissionDenied):
        update_user(actor, target, pin="481926")
    target.refresh_from_db()
    assert target.role == "SUPERADMIN"


def test_stale_actor_cannot_keep_permissions_after_demotion():
    actor = User.objects.create_user(username="stale-actor", role="ADMIN")
    User.objects.filter(pk=actor.pk).update(role="EMPLOYEE")
    with pytest.raises(PermissionDenied):
        require_role(actor, "ADMIN")


def test_stale_service_actor_is_revoked_after_credential_reset():
    actor = User.objects.create_user(username="cached-service-actor")
    owner = User.objects.create_user(username="reset-owner", role="SUPERADMIN")
    update_user(owner, actor, pin="481926")
    with pytest.raises(PermissionDenied):
        require_role(actor, "EMPLOYEE")


def test_post_account_cannot_bypass_superadmin_pii_guard():
    request = RequestFactory().post("/tpv/cuentas/1/")
    request.user = User.objects.create_user(username="post-pii", role="SUPERADMIN")
    request.session = {"elevated_until": (timezone.now() + timedelta(minutes=10)).timestamp()}
    assert (
        SupportPIIMiddleware(lambda request: HttpResponse("Customer data"))(request).status_code
        == 403
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_nonfinite_or_boolean_elevation_expiry_is_not_valid(value):
    request = RequestFactory().get("/soporte/")
    request.session = {"elevated_until": value}
    with pytest.raises(PermissionDenied):
        require_elevated(request)


@pytest.mark.parametrize("role", User.Role.values)
@pytest.mark.parametrize(
    "path,minimum",
    [
        ("/tpv/", "EMPLOYEE"),
        ("/caja/", "EMPLOYEE"),
        ("/clientes/", "EMPLOYEE"),
        ("/facturas/", "EMPLOYEE"),
        ("/catalogo/", "ADMIN"),
        ("/informes/", "MANAGER"),
        ("/empresa/", "ADMIN"),
        ("/plano/configuracion/", "ADMIN"),
        ("/usuarios/", "ADMIN"),
        ("/auditoria/", "ADMIN"),
        ("/soporte/", "SUPERADMIN"),
    ],
)
def test_four_role_url_matrix_with_elevation_and_pii_approval(client, role, path, minimum):
    from apps.accounts.permissions import ROLE_RANK
    from apps.support.models import SupportSession

    user = User.objects.create_user(username="matrix-user", role=role)
    owner = User.objects.create_user(username="matrix-owner", role="ADMIN")
    if role == "SUPERADMIN":
        SupportSession.objects.create(
            actor=user,
            approved_by=owner,
            scope="PII",
            justification="Auditoría de rutas",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
    client.force_login(user)
    session = client.session
    session["elevated_until"] = (timezone.now() + timedelta(minutes=10)).timestamp()
    session.save()
    expected = 200 if ROLE_RANK[role] >= ROLE_RANK[minimum] else 403
    assert client.get(path).status_code == expected


@pytest.mark.parametrize(
    "path",
    ["/empresa/", "/usuarios/", "/auditoria/", "/soporte/", "/catalogo/", "/plano/configuracion/"],
)
def test_privileged_routes_reject_pin_only_superadmin(client, path):
    user = User.objects.create_user(username="pin-not-elevated", role="SUPERADMIN")
    client.force_login(user)
    assert client.get(path).status_code == 403


@pytest.mark.parametrize("path", ["/catalogo/", "/plano/configuracion/"])
def test_pin_only_admin_cannot_access_admin_catalog_or_layout(client, path):
    user = User.objects.create_user(username="pin-only-admin", role="ADMIN")
    client.force_login(user)
    assert client.get(path).status_code == 403


def test_security_change_revokes_approver_support_grants():
    from apps.support.models import SupportSession

    support = User.objects.create_user(username="support-revoke", role="SUPERADMIN")
    owner = User.objects.create_user(
        username="owner-revoke", role="ADMIN", password="Some!Passphrase947"
    )
    approval = SupportSession.objects.create(
        actor=support,
        approved_by=owner,
        scope="PII",
        justification="Prueba revocación",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    update_user(support, owner, pin="481926")
    approval.refresh_from_db()
    assert approval.revoked_at is not None


def test_disable_then_reenable_does_not_resurrect_old_session(client):
    user = User.objects.create_user(username="reactivated")
    owner = User.objects.create_user(username="owner-reactivate", role="SUPERADMIN")
    client.force_login(user)
    update_user(owner, user, active=False)
    update_user(owner, user, active=True)
    assert client.get("/tpv/").status_code == 403


def test_locked_origin_cannot_create_unlimited_account_throttle_rows():
    from apps.accounts.models import LoginThrottle
    from apps.accounts.services import authenticate_local

    for number in range(5):
        assert authenticate_local(f"unknown-{number}", "481926", "same-terminal") is None
    count = LoginThrottle.objects.count()
    for number in range(5, 10):
        assert authenticate_local(f"unknown-{number}", "481926", "same-terminal") is None
    assert LoginThrottle.objects.count() == count


def test_admin_post_requires_csrf_and_logout_is_post_only():
    from django.test import Client

    client = Client(enforce_csrf_checks=True)
    user = User.objects.create_user(username="csrf-admin", role="ADMIN")
    client.force_login(user)
    assert client.post("/usuarios/", {"username": "forged"}).status_code == 403
    assert client.get("/salir/").status_code == 405
    assert not User.objects.filter(username="forged").exists()


def test_password_forms_preserve_exact_whitespace():
    from apps.accounts.forms import ElevateForm, LoginForm

    password = "  Exact!Password947  "
    login = LoginForm({"username": "exact-user", "credential": password, "password_mode": True})
    assert login.is_valid()
    assert login.cleaned_data["credential"] == password
    elevation = ElevateForm({"password": password})
    assert elevation.is_valid()
    assert elevation.cleaned_data["password"] == password


@pytest.mark.parametrize("role", User.Role.values)
def test_menu_links_follow_role_matrix(client, role):
    user = User.objects.create_user(username="menu-matrix", role=role)
    client.force_login(user)
    response = client.get("/tpv/")
    html = response.content.decode()
    admin = role in ("ADMIN", "SUPERADMIN")
    assert ('href="/usuarios/"' in html) is admin
    assert ('href="/catalogo/"' in html) is admin
    assert ('href="/soporte/"' in html) is (role == "SUPERADMIN")
    assert ('href="/informes/"' in html) is (role != "EMPLOYEE")


def test_login_validates_terminal_and_clears_previous_assignment(client):
    from apps.audit.models import AuditEvent
    from apps.core.models import Terminal

    terminal = Terminal.objects.create(code="front", name="Recepción")
    inactive = Terminal.objects.create(code="disabled", name="Desactivado", active=False)
    user = User.objects.create_user(username="terminal-login")
    user.set_pin("481926")
    user.save()
    payload = {"username": user.username, "credential": "481926", "terminal": inactive.pk}
    assert client.post("/acceso/", payload).status_code == 200
    assert "_auth_user_id" not in client.session
    payload["terminal"] = terminal.pk
    assert client.post("/acceso/", payload).status_code == 302
    assert client.session["terminal_id"] == terminal.pk
    event = AuditEvent.objects.filter(action="auth.pin").first()
    assert event.metadata["terminal_id"] == terminal.pk
    payload.pop("terminal")
    assert client.post("/acceso/", payload).status_code == 302
    assert "terminal_id" not in client.session


def test_terminal_context_is_validated_and_does_not_leak_between_requests():
    from apps.accounts.middleware import TerminalContextMiddleware
    from apps.audit.models import AuditEvent
    from apps.audit.services import record
    from apps.core.models import Terminal

    terminal = Terminal.objects.create(code="context", name="Contexto")
    user = User.objects.create_user(username="terminal-context")
    request = RequestFactory().get("/tpv/")
    request.user = user
    request.session = {"terminal_id": terminal.pk}

    def downstream(request):
        record(user, "terminal.test", metadata={"terminal_id": 987654})
        assert request.terminal == terminal
        return HttpResponse("OK")

    middleware = TerminalContextMiddleware(downstream)
    assert middleware(request).status_code == 200
    assert (
        AuditEvent.objects.filter(action="terminal.test").get().metadata["terminal_id"]
        == terminal.pk
    )
    terminal.refresh_from_db()
    assert terminal.last_seen_at is not None
    first_seen = terminal.last_seen_at
    middleware(request)
    terminal.refresh_from_db()
    assert terminal.last_seen_at == first_seen
    outside = record(user, "outside.request")
    assert "terminal_id" not in outside.metadata
    terminal.active = False
    terminal.save()
    checked = []
    middleware = TerminalContextMiddleware(
        lambda req: checked.append(req.terminal) or HttpResponse("OK")
    )
    middleware(request)
    assert checked == [None]
    assert "terminal_id" not in request.session


def test_sqlite_replace_cannot_rewrite_audit_evidence():
    from django.db import IntegrityError, connection, transaction

    from apps.audit.services import record

    event = record(action="immutable-original")
    with pytest.raises(IntegrityError), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO audit_auditevent "
                "(id, action, target, outcome, metadata, created_at, actor_id) "
                "SELECT id, 'rewritten', target, outcome, metadata, created_at, actor_id "
                "FROM audit_auditevent WHERE id=%s",
                [event.pk],
            )
    event.refresh_from_db()
    assert event.action == "immutable-original"


def test_demotion_clears_inherited_django_superuser_capabilities():
    controller = User.objects.create_user(username="demotion-controller", role="SUPERADMIN")
    former = User.objects.create_superuser(
        username="former-superuser", password="Non-default-secure-password-874!"
    )
    update_user(controller, former, role="EMPLOYEE")
    former.refresh_from_db()
    assert not former.is_superuser and not former.is_staff
    assert not former.has_perm("billing.change_invoice")
