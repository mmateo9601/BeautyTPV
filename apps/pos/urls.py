from django.urls import path

from . import views

app_name = "pos"
urlpatterns = [
    path("", views.floor, name="floor"),
    path("venta-rapida/", views.quick_sale, name="quick_sale"),
    path("cuentas/<int:pk>/preparar-cobro/", views.prepare_payment, name="prepare_payment"),
    path("cuentas/<int:pk>/reanudar/", views.resume_ticket, name="resume_ticket"),
    path("puestos/<int:pk>/", views.open_station, name="open_station"),
    path("cuentas/<int:pk>/", views.ticket, name="ticket"),
    path("cuentas/<int:pk>/lineas/", views.add_line, name="add_line"),
    path("lineas/<int:pk>/", views.update_line, name="update_line"),
    path("lineas/<int:pk>/eliminar/", views.remove_line, name="remove_line"),
    path("cuentas/<int:pk>/anular/", views.cancel_ticket, name="cancel_ticket"),
    path("cuentas/<int:pk>/cliente/", views.customer, name="customer"),
    path("cuentas/<int:pk>/cobrar/", views.checkout, name="checkout"),
]
