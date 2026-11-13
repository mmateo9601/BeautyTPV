from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.utils import timezone

from apps.audit.services import record

from .permissions import require_elevated


class SupportPIIMiddleware:
    """Require explicit, independent approval for technical superadmin PII access."""

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def sensitive(request):
        path = request.path_info
        return (
            path.startswith(("/clientes/", "/facturas/", "/informes/"))
            or (request.method in ("GET", "HEAD") and path.startswith("/tpv/cuentas/"))
            or (request.method == "POST" and path.startswith("/hardware/facturas/"))
        )

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and user.role == "SUPERADMIN" and self.sensitive(request):
            from apps.support.models import SupportSession

            authorized = None
            try:
                require_elevated(request)
                authorized = (
                    SupportSession.objects.filter(
                        actor=user,
                        scope="PII",
                        revoked_at__isnull=True,
                        expires_at__gt=timezone.now(),
                        approved_by__is_active=True,
                        approved_by__role__in=("ADMIN", "SUPERADMIN"),
                    )
                    .exclude(approved_by=user)
                    .first()
                )
            except PermissionDenied:
                pass
            if authorized is None:
                record(user, "support.pii_denied", target=request.path_info, outcome="DENIED")
                return HttpResponseForbidden(
                    "Acceso a datos personales: confirme su contraseña y autorice una sesión "
                    "de soporte con alcance PII en /soporte/. Debe aprobar otro administrador."
                )
            record(
                user,
                "support.pii_authorized",
                target=request.path_info,
                metadata={"session_id": authorized.pk, "scope": "PII"},
            )
        return self.get_response(request)
