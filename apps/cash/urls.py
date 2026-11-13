from django.urls import path

from . import views

app_name = "cash"
urlpatterns = [
    path("", views.index, name="index"),
    path("abrir/", views.open, name="open"),
    path("<int:pk>/movimiento/", views.movement, name="movement"),
    path("<int:pk>/cerrar/", views.close, name="close"),
]
