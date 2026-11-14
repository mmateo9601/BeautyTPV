from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import require_role
from apps.accounts.services import revoke_user_sessions
from apps.audit.models import AuditEvent
from apps.support.models import SupportSession

pytestmark = pytest.mark.django_db


def make_user(name, role="EMPLOYEE"):
    user = User.objects.create_user(username=name, role=role, password="Exact password 847!")
    user.set_pin("739184")
    user.save()
    return user


def test_explicit_revocation_invalidates_multiple_sessions_without_changing_credentials():
    actor = make_user("revoker", "ADMIN")
    target = make_user("operator")
    before = (target.pin_hash, target.password, target.auth_version)
    browsers = [Client(), Client()]
    for browser in browsers:
        browser.force_login(target)
        assert browser.get("/tpv/").status_code == 200
    current = revoke_user_sessions(actor, target)
    assert (current.pin_hash, current.password) == before[:2]
    assert current.auth_version == before[2] + 1
    for browser in browsers:
        assert browser.get("/tpv/").status_code == 403
    assert current.check_pin("739184") and current.check_password("Exact password 847!")
    browsers[0].force_login(current)
    assert browsers[0].get("/tpv/").status_code == 200
    event = AuditEvent.objects.get(action="user.sessions_revoked")
    assert event.actor == actor and event.target.endswith(f":{target.pk}")
    assert "739184" not in str(event.metadata)
    with pytest.raises(PermissionDenied):
        require_role(target)


@pytest.mark.parametrize("role", ["EMPLOYEE", "MANAGER", "ADMIN"])
def test_service_revocation_denies_insufficient_or_equal_rank(role):
    actor = make_user("lower", role)
    target = make_user("protected", "ADMIN")
    with pytest.raises(PermissionDenied):
        revoke_user_sessions(actor, target)
    target.refresh_from_db()
    assert target.auth_version == 0
    assert not AuditEvent.objects.filter(action="user.sessions_revoked").exists()


def test_revocation_refreshes_promoted_target_and_demoted_actor():
    actor = make_user("admin", "ADMIN")
    target = make_user("target")
    User.objects.filter(pk=target.pk).update(role="SUPERADMIN")
    with pytest.raises(PermissionDenied):
        revoke_user_sessions(actor, target)
    User.objects.filter(pk=actor.pk).update(role="EMPLOYEE")
    with pytest.raises(PermissionDenied):
        revoke_user_sessions(actor, make_user("another"))


@pytest.mark.parametrize("change", [{"is_active": False}, {"auth_version": 1}])
def test_revocation_rejects_disabled_or_revoked_cached_actor(change):
    actor = make_user("cached-admin", "ADMIN")
    User.objects.filter(pk=actor.pk).update(**change)
    with pytest.raises(PermissionDenied):
        revoke_user_sessions(actor, make_user("recipient"))


def test_superadmin_revocation_cancels_grants_as_actor_and_approver():
    actor = make_user("root", "SUPERADMIN")
    target = make_user("other-root", "SUPERADMIN")
    independent = make_user("approver", "ADMIN")
    for grant_actor, approver in [(target, independent), (actor, target)]:
        SupportSession.objects.create(
            actor=grant_actor,
            approved_by=approver,
            justification="Prueba sintética de revocación",
            scope="TECHNICAL",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
    revoke_user_sessions(actor, target)
    assert not SupportSession.objects.filter(revoked_at__isnull=True).exists()
    assert AuditEvent.objects.get(action="user.sessions_revoked").metadata["count"] == 2


def test_superadmin_can_revoke_own_sessions_and_must_authenticate_again(client):
    actor = make_user("self-root", "SUPERADMIN")
    client.force_login(actor)
    revoke_user_sessions(actor, actor)
    assert client.get("/soporte/").status_code == 403
