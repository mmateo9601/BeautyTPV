from django.urls import path

from . import views

app_name = "billing"
urlpatterns = [
    path("", views.invoice_list, name="index"),
    path("", views.invoice_list, name="list"),
    path("<int:pk>/", views.invoice_detail, name="detail"),
    path("<int:pk>/pdf/", views.invoice_pdf, name="pdf"),
    path("<int:pk>/rectificar/", views.rectify, name="rectify"),
    path("<int:pk>/reimprimir/", views.reprint, name="reprint"),
]
