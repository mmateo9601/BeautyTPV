from django.urls import path

from . import views

app_name = "team"
urlpatterns = [
    path("<int:pk>/revocar-sesiones/", views.revoke_user_sessions, name="revoke_sessions"),
    path("<int:pk>/desbloquear/", views.unlock_user, name="unlock"),
    path("", views.users, name="index"),
    path("<int:pk>/", views.user_edit, name="edit"),
]
