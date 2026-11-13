from django.urls import path

from . import views

app_name = "layout"
urlpatterns = [
    path("", views.index, name="index"),
    path("secciones/", views.section_create, name="section_create"),
    path("puestos/nuevo/", views.station_edit, name="station_create"),
    path("puestos/<int:pk>/editar/", views.station_edit, name="station_edit"),
    path("puestos/<int:pk>/eliminar/", views.station_delete, name="station_delete"),
]
