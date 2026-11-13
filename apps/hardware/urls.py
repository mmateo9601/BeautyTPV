from django.urls import path

from . import bridge, views

app_name = "hardware"
urlpatterns = [
    path("bridge/<int:terminal_pk>/claim/", bridge.claim, name="bridge_claim"),
    path("bridge/<int:terminal_pk>/jobs/<int:job_pk>/ack/", bridge.acknowledge, name="bridge_ack"),
    path("facturas/<int:pk>/copia/", views.reprint, name="reprint"),
    path("impresoras/<int:pk>/prueba/", views.test_printer, name="test"),
    path("trabajos/<int:pk>/reintentar/", views.retry, name="retry"),
]
