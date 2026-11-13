import hashlib
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record

from .models import LoginThrottle, User
from .permissions import ROLE_RANK, require_role


def _throttle_keys(username, origin):
    return [hashlib.sha256(value.encode()).hexdigest() for value in (f"user:{username.casefold()}", f"origin:{origin}")]


@transaction.atomic
def authenticate_local(username, credential, origin, *, password=False, request=None):
    gates = [LoginThrottle.objects.get_or_create(key=key)[0] for key in _throttle_keys(username, origin)]
    if any(gate.locked for gate in gates):
        record(action="auth.locked", outcome="DENIED")
        return None
    user = User.objects.filter(username=username, is_active=True).first()
    if password:
        user = authenticate(request=request, username=username, password=credential)
        valid = user is not None
    else:
        valid = user is not None and user.check_pin(credential)
    if not valid:
        for gate in gates:
            # A completed lock window starts a fresh attempt budget.
            if gate.locked_until and gate.locked_until <= timezone.now():
                gate.failures = 0
                gate.locked_until = None
            gate.fail()
        record(action="auth.failed", outcome="DENIED")
        return None
    for gate in gates:
        gate.failures = 0
        gate.locked_until = None
        gate.save()
    record(actor=user, action="auth.password" if password else "auth.pin")
    return user


def authorize_user_change(actor, target=None, role=None):
    require_role(actor, "ADMIN")
    desired = role or (target.role if target else "EMPLOYEE")
    if desired not in User.Role.values:
        raise ValidationError("Rol inválido.")
    if actor.role != "SUPERADMIN":
        if ROLE_RANK[desired] >= ROLE_RANK[actor.role] or (target and ROLE_RANK[target.role] >= ROLE_RANK[actor.role]):
            raise PermissionDenied("Solo puede administrar usuarios de rango inferior.")


@transaction.atomic
def create_user(actor, *, username, role="EMPLOYEE", pin=None, password=None, first_name=""):
    authorize_user_change(actor, role=role)
    user = User(username=username, role=role, first_name=first_name)
    if role in ("ADMIN", "SUPERADMIN") and not password:
        raise ValidationError("Los perfiles administrativos requieren contraseña.")
    if password:
        validate_password(password, user)
        user.set_password(password)
    else:
        user.set_unusable_password()
    if pin:
        user.set_pin(pin)
    user.full_clean()
    user.save()
    record(actor, "user.created", obj=user, metadata={"role": role})
    return user


@transaction.atomic
def update_user(actor, target, *, role=None, active=None, pin=None, password=None):
    authorize_user_change(actor, target, role)
    if target.pk == actor.pk and (active is False or (role and role != actor.role)):
        raise PermissionDenied("No puede desactivar ni degradar su propia sesión.")
    previous = target.role
    if role:
        target.role = role
    if active is not None:
        target.is_active = active
    if password:
        validate_password(password, target)
        target.set_password(password)
    if target.role in ("ADMIN", "SUPERADMIN") and not target.has_usable_password():
        raise ValidationError("El perfil administrativo requiere contraseña.")
    if pin:
        target.set_pin(pin)
        for key in _throttle_keys(target.username, "")[:1]:
            LoginThrottle.objects.filter(key=key).update(failures=0, locked_until=None)
    target.full_clean()
    target.save()
    record(actor, "user.updated", obj=target, metadata={"role": target.role, "previous_role": previous})
    return target


def elevation_expiry():
    return (timezone.now() + timedelta(minutes=10)).timestamp()
