from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.index, name="index"),
    path("nuevo/", views.edit, name="create"),
    path("<int:pk>/editar/", views.edit, name="edit"),
    path("categorias/", views.category, name="category"),
]
