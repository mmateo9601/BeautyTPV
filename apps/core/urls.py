from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.settings, name="settings"),
    path("logo/", views.logo, name="logo"),
    path("logo/guardar/", views.logo_save, name="logo_save"),
]
