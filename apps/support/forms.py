from django import forms

from apps.accounts.models import User
from apps.hardware.models import Printer

from .models import TechnicalSettings


class PrinterForm(forms.ModelForm):
    class Meta:
        model = Printer
        fields = [
            "name",
            "connection_type",
            "address",
            "port",
            "usb_vendor",
            "usb_product",
            "usb_endpoint",
            "encoding",
            "codepage",
            "enabled",
        ]


class TechnicalSettingsForm(forms.ModelForm):
    class Meta:
        model = TechnicalSettings
        fields = ["backup_retention_days", "backup_interval_hours"]


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150, label="Usuario")
    first_name = forms.CharField(required=False, label="Nombre")
    role = forms.ChoiceField(choices=User.Role.choices, label="Rol")
    pin = forms.CharField(required=False, widget=forms.PasswordInput, label="PIN de 6 a 12 dígitos")
    password = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Contraseña administrativa"
    )


class UserUpdateForm(forms.Form):
    role = forms.ChoiceField(choices=User.Role.choices, label="Rol")
    active = forms.BooleanField(required=False, label="Activo")
    pin = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Nuevo PIN (vacío conserva)"
    )
    password = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Nueva contraseña (vacío conserva)"
    )
