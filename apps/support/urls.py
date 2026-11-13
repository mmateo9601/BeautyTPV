from django.urls import path

from . import views

app_name = "support"
urlpatterns = [
    path("restauracion/", views.restore_advisor, name="restore_advisor"),
    path("terminales/", views.terminals, name="terminals"),
    path("terminales/<int:pk>/", views.terminal_edit, name="terminal_edit"),
    path("fiscal/", views.fiscal_settings, name="fiscal_settings"),
    path("logs/", views.logs, name="logs"),
    path("", views.index, name="index"),
    path("autorizacion/", views.authorize, name="authorize"),
    path("autorizacion/<int:pk>/revocar/", views.revoke, name="revoke"),
    path("diagnostico/", views.diagnostic, name="diagnostic"),
    path("diagnostico/exportar/", views.export_diagnostics, name="diagnostics_export"),
    path("backup/", views.backup, name="backup"),
    path("backup/<int:pk>/descargar/", views.backup_download, name="backup_download"),
    path("dispositivos/", views.printer_save, name="printer_save"),
    path("dispositivos/<int:pk>/", views.printer_save, name="printer_edit"),
    path("fiscal/<int:pk>/recuperar/", views.recover_fiscal, name="recover_fiscal"),
    path("fiscal/<int:pk>/subsanar/", views.correct_fiscal, name="correct_fiscal"),
    path("fiscal/<int:pk>/anular/", views.annul_fiscal, name="annul_fiscal"),
    path("ajustes/", views.technical_settings, name="settings"),
    path("actualizaciones/", views.updates, name="updates"),
]
