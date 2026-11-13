from django.urls import path

from . import views

app_name = "pos"
urlpatterns = [
    path("", views.floor, name="floor"),
    path("puestos/<int:pk>/", views.open_station, name="open_station"),
    path("cuentas/<int:pk>/", views.ticket, name="ticket"),
    path("cuentas/<int:pk>/lineas/", views.add_line, name="add_line"),
    path("lineas/<int:pk>/", views.update_line, name="update_line"),
    path("lineas/<int:pk>/eliminar/", views.remove_line, name="remove_line"),
    path("cuentas/<int:pk>/anular/", views.cancel_ticket, name="cancel_ticket"),
    path("cuentas/<int:pk>/cliente/", views.customer, name="customer"),
    path("cuentas/<int:pk>/cobrar/", views.checkout, name="checkout"),
]
