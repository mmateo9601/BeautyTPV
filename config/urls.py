from django.shortcuts import redirect
from django.urls import include, path

from .views import health

urlpatterns = [
    path("", lambda request: redirect("/tpv/")),
    path("", include("apps.accounts.urls")),
    path("auditoria/", include("apps.audit.urls")),
    path("tpv/", include("apps.pos.urls")),
    path("plano/configuracion/", include("apps.layout.urls")),
    path("catalogo/", include("apps.catalog.urls")),
    path("clientes/", include("apps.customers.urls")),
    path("caja/", include("apps.cash.urls")),
    path("facturas/", include("apps.billing.urls")),
    path("hardware/", include("apps.hardware.urls")),
    path("empresa/", include("apps.core.urls")),
    path("informes/", include("apps.reports.urls")),
    path("soporte/", include("apps.support.urls")),
    path("usuarios/", include("apps.support.user_urls")),
    path("health/", health, name="health"),
]
