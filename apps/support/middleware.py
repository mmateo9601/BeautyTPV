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
            if hold_path(settings.DATABASES["default"]["NAME"]).exists():
                return HttpResponse(
                    "Restauración pendiente de conciliación fiscal. Operativa bloqueada; contacte con Superadmin.",
                    status=503,
                )
        return self.get_response(request)
