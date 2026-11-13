from functools import wraps

from django.core.exceptions import PermissionDenied
from django.utils import timezone

ROLE_RANK = {"EMPLOYEE": 10, "MANAGER": 20, "ADMIN": 30, "SUPERADMIN": 40}


def require_role(user, minimum="EMPLOYEE"):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        raise PermissionDenied("Acceso no autorizado.")
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get(str(minimum), 100):
        raise PermissionDenied("Permisos insuficientes.")
    return user


def require_elevated(request):
    until = request.session.get("elevated_until", 0)
    if not isinstance(until, (int, float)) or until <= timezone.now().timestamp():
        raise PermissionDenied("Confirme su contraseña para esta operación.")


def role_required(minimum="EMPLOYEE", elevated=False):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            require_role(request.user, minimum)
            if elevated:
                require_elevated(request)
            return view(request, *args, **kwargs)

        return wrapped

    return decorate
