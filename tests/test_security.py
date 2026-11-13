from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts.models import LoginThrottle, User
from apps.accounts.permissions import require_elevated, require_role
from apps.accounts.services import authenticate_local, create_user, update_user
from apps.audit.models import AuditEvent
from apps.audit.services import record

pytestmark = pytest.mark.django_db


@pytest.fixture
def users():
    return {
        role: User.objects.create_user(username=role.lower(), role=role)
        for role in User.Role.values
    }


@pytest.mark.parametrize("actor", User.Role.values)
@pytest.mark.parametrize("minimum", User.Role.values)
def test_role_matrix(users, actor, minimum):
    ranks = User.Role.values
    if ranks.index(actor) >= ranks.index(minimum):
        assert require_role(users[actor], minimum) == users[actor]
    else:
        with pytest.raises(PermissionDenied):
            require_role(users[actor], minimum)


def test_inactive_anonymous_and_unknown_roles_fail(users):
    with pytest.raises(PermissionDenied):
        require_role(AnonymousUser())
    user = users["SUPERADMIN"]
    user.is_active = False
    with pytest.raises(PermissionDenied):
        require_role(user)
    user.is_active = True
    with pytest.raises(PermissionDenied):
        require_role(user, "CLIENT")


def test_pin_is_hashed_and_bad_pin_is_rejected(users):
    user = users["EMPLOYEE"]
    user.set_pin("839216")
    user.save()
    assert user.pin_hash != "839216"
    assert user.check_pin("839216")
    assert not user.check_pin("000000")
    for pin in ("123", "abcdef", "１２３４５６", "1" * 13):
        with pytest.raises(ValidationError):
            user.set_pin(pin)


def test_pin_bruteforce_blocks_across_origins(users):
    user = users["EMPLOYEE"]
    user.set_pin("839216")
    user.save()
    for number in range(5):
        assert authenticate_local(user.username, "000000", f"terminal-{number}") is None
    assert authenticate_local(user.username, "839216", "different-terminal") is None
    LoginThrottle.objects.update(locked_until=timezone.now() - timedelta(seconds=1))
    assert authenticate_local(user.username, "839216", "different-terminal") == user


def test_admin_cannot_promote_or_edit_peer(users):
    admin = users["ADMIN"]
    for role in ("ADMIN", "SUPERADMIN"):
        with pytest.raises(PermissionDenied):
            create_user(admin, username="escalation", role=role, password="Fresh!ComplexPass541")
    with pytest.raises(PermissionDenied):
        update_user(admin, users["SUPERADMIN"], active=False)
    with pytest.raises(PermissionDenied):
        update_user(admin, admin, pin="839216")
    assert User.objects.filter(username="escalation").count() == 0


def test_superadmin_can_create_privileged_user_without_default_credentials(users):
    with pytest.raises(ValidationError):
        create_user(users["SUPERADMIN"], username="technical", role="SUPERADMIN")
    user = create_user(
        users["SUPERADMIN"],
        username="technical",
        role="SUPERADMIN",
        password="Fresh!ComplexPass541",
    )
    assert user.check_password("Fresh!ComplexPass541")
    assert not user.pin_hash


def test_audit_is_append_only_and_metadata_allowlisted(users):
    event = record(
        users["ADMIN"],
        "test",
        metadata={
            "password": "SECRET",
            "pin": "839216",
            "card_number": "4111111111111111",
            "status": "OK",
            "nested": {"token": "secret"},
        },
    )
    assert event.metadata == {"status": "OK"}
    with pytest.raises(ValidationError):
        AuditEvent.objects.filter(pk=event.pk).update(action="altered")
    with pytest.raises(ValidationError):
        event.save()
    with pytest.raises(ValidationError):
        event.delete()
    with pytest.raises(ValidationError):
        AuditEvent.objects.filter(pk=event.pk).delete()


def test_elevated_session_expires():
    request = RequestFactory().get("/soporte/")
    request.session = {}
    with pytest.raises(PermissionDenied):
        require_elevated(request)
    request.session["elevated_until"] = (timezone.now() + timedelta(minutes=1)).timestamp()
    require_elevated(request)
    request.session["elevated_until"] = (timezone.now() - timedelta(seconds=1)).timestamp()
    with pytest.raises(PermissionDenied):
        require_elevated(request)


def test_createsuperuser_assigns_internal_superadmin():
    user = User.objects.create_superuser("root-test", password="Fresh!ComplexPass541")
    assert user.role == "SUPERADMIN"
    assert user.is_superuser


def test_pin_relogin_clears_previous_elevation(client):
    user = User.objects.create_user(username="pin-again", role="SUPERADMIN")
    user.set_pin("839216")
    user.save()
    client.force_login(user)
    session = client.session
    session["elevated_until"] = (timezone.now() + timedelta(minutes=10)).timestamp()
    session.save()
    response = client.post("/acceso/", {"username": user.username, "credential": "839216"})
    assert response.status_code == 302
    assert "elevated_until" not in client.session


def test_audit_bulk_upsert_cannot_rewrite_evidence():
    from django.db import IntegrityError, transaction

    event = record(action="original")
    with pytest.raises(IntegrityError), transaction.atomic():
        AuditEvent.objects.bulk_create(
            [AuditEvent(pk=event.pk, action="altered")],
            update_conflicts=True,
            update_fields=["action"],
            unique_fields=["id"],
        )
    event.refresh_from_db()
    assert event.action == "original"


def test_audit_preserves_only_valid_evidence_digest():
    digest = "a" * 64
    event = record(action="restore.reconciled", metadata={"sha256": digest})
    assert event.metadata == {"sha256": digest}
    invalid = record(action="restore.reconciled", metadata={"sha256": "secret-path"})
    assert invalid.metadata == {}


def test_support_pii_requires_elevation_and_independent_live_approval():
    from django.http import HttpResponse

    from apps.accounts.middleware import SupportPIIMiddleware
    from apps.support.models import SupportSession

    actor = User.objects.create_user(username="technical-pii", role="SUPERADMIN")
    approver = User.objects.create_user(username="owner-pii", role="ADMIN")
    request = RequestFactory().get("/clientes/")
    request.user = actor
    request.session = {}
    middleware = SupportPIIMiddleware(lambda request: HttpResponse("allowed"))
    assert middleware(request).status_code == 403
    request.session["elevated_until"] = (timezone.now() + timedelta(minutes=10)).timestamp()
    assert middleware(request).status_code == 403
    approval = SupportSession.objects.create(
        actor=actor,
        approved_by=approver,
        justification="Revisión solicitada por propietario",
        scope="PII",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    assert middleware(request).status_code == 200
    approval.approved_by = actor
    approval.save()
    assert middleware(request).status_code == 403
    approval.approved_by = approver
    approval.expires_at = timezone.now() - timedelta(seconds=1)
    approval.save()
    assert middleware(request).status_code == 403
    assert AuditEvent.objects.filter(action="support.pii_authorized").count() == 1


@pytest.mark.parametrize("role", ["EMPLOYEE", "MANAGER", "ADMIN"])
def test_operational_roles_do_not_require_technical_pii_approval(role):
    from django.http import HttpResponse

    from apps.accounts.middleware import SupportPIIMiddleware

    request = RequestFactory().get("/clientes/")
    request.user = User.objects.create_user(username=f"normal-{role}", role=role)
    request.session = {}
    assert SupportPIIMiddleware(lambda request: HttpResponse("allowed"))(request).status_code == 200


@pytest.mark.parametrize(
    "method,path,expected",
    [
        ("get", "/tpv/cuentas/1/", True),
        ("post", "/hardware/facturas/1/copia/", True),
        ("get", "/facturas/1/pdf/", True),
        ("get", "/informes/", True),
        ("get", "/tpv/", False),
        ("get", "/soporte/", False),
    ],
)
def test_support_pii_route_coverage(method, path, expected):
    from apps.accounts.middleware import SupportPIIMiddleware

    request = getattr(RequestFactory(), method)(path)
    assert SupportPIIMiddleware.sensitive(request) is expected
