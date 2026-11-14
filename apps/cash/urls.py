from django.urls import path

from . import views

app_name = "cash"
urlpatterns = [
    path("configuracion/", views.registers, name="registers"),
    path("configuracion/nueva/", views.register_create, name="register_create"),
    path("configuracion/<int:pk>/", views.register_edit, name="register_edit"),
    path("", views.index, name="index"),
    path("abrir/", views.open, name="open"),
    path("<int:pk>/movimiento/", views.movement, name="movement"),
    path("<int:pk>/cerrar/", views.close, name="close"),
]
