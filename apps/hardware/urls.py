from django.urls import path

from . import views

app_name = "hardware"
urlpatterns = [
    path("facturas/<int:pk>/copia/", views.reprint, name="reprint"),
    path("impresoras/<int:pk>/prueba/", views.test_printer, name="test"),
    path("trabajos/<int:pk>/reintentar/", views.retry, name="retry"),
]
