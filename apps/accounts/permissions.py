import math
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.utils import timezone

ROLE_RANK = {"EMPLOYEE": 10, "MANAGER": 20, "ADMIN": 30, "SUPERADMIN": 40}


def require_role(user, minimum="EMPLOYEE"):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        raise PermissionDenied("Acceso no autorizado.")
    from .models import User

    current = (
        User.objects.filter(pk=user.pk, is_active=True)
        .only("role", "is_active", "auth_version")
        .first()
    )
    if (
        current is None
        or current.auth_version != user.auth_version
        or ROLE_RANK.get(current.role, 0) < ROLE_RANK.get(str(minimum), 100)
    ):
        raise PermissionDenied("Permisos insuficientes.")
    # Callers often inspect actor.role again after this check. Never leave them
    # using an object cached before another administrator changed its role.
    user.role = current.role
    return user


def require_elevated(request):
    until = request.session.get("elevated_until", 0)
    if (
        type(until) not in (int, float)
        or not math.isfinite(until)
        or until <= timezone.now().timestamp()
    ):
        raise PermissionDenied("Confirme su contraseña para esta operación.")


def role_required(minimum="EMPLOYEE", elevated=False):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            require_role(request.user, minimum)
            if elevated or ROLE_RANK.get(str(minimum), 0) >= ROLE_RANK["ADMIN"]:
                require_elevated(request)
            return view(request, *args, **kwargs)

        return wrapped

    return decorate
