from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.utils import timezone

from apps.audit.context import terminal_context
from apps.audit.services import record

from .permissions import require_elevated


class TerminalContextMiddleware:
    """Validated browser terminal attribution; never authenticates a bridge/device."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.db.models import Q

        from apps.core.models import Terminal

        terminal_id = request.session.get("terminal_id")
        terminal = None
        if type(terminal_id) is int and terminal_id > 0:
            terminal = Terminal.objects.filter(pk=terminal_id, active=True).first()
        if terminal is None and terminal_id is not None:
            request.session.pop("terminal_id", None)
        request.terminal = terminal
        if terminal and request.user.is_authenticated:
            now = timezone.now()
            cutoff = now - timedelta(minutes=1)
            if terminal.last_seen_at is None or terminal.last_seen_at < cutoff:
                Terminal.objects.filter(pk=terminal.pk).filter(
                    Q(last_seen_at__isnull=True) | Q(last_seen_at__lt=cutoff)
                ).update(last_seen_at=now)
        with terminal_context(terminal.pk if terminal else None):
            return self.get_response(request)


class SupportPIIMiddleware:
    """Require explicit, independent approval for technical superadmin PII access."""

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def sensitive(request):
        path = request.path_info
        return (
            path.startswith(("/clientes/", "/facturas/", "/informes/"))
            or path.startswith("/tpv/cuentas/")
            or path.startswith("/hardware/facturas/")
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
