from django.conf import settings
from django.http import HttpResponse

from .operations import hold_path


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ("GET", "HEAD", "OPTIONS") and request.path.startswith(
            ("/tpv/", "/caja/", "/facturas/")
        ):
            from .models import TechnicalSettings

            if (
                hold_path(settings.DATABASES["default"]["NAME"]).exists()
                or TechnicalSettings.load().maintenance
            ):
                return HttpResponse(
                    "Mantenimiento o conciliación fiscal pendiente. Operativa bloqueada; contacte con Superadmin.",
                    status=503,
                )
        return self.get_response(request)
