from django.urls import path

from . import views

app_name = "customers"
urlpatterns = [
    path("", views.index, name="index"),
    path("nuevo/", views.edit, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/editar/", views.edit, name="edit"),
    path("<int:pk>/eliminar/", views.delete, name="delete"),
]
