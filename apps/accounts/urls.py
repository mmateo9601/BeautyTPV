from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [path("acceso/", views.login_view, name="login"), path("salir/", views.logout_view, name="logout"), path("elevar/", views.elevate_view, name="elevate")]
