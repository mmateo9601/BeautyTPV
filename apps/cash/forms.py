from django import forms

from .models import CashRegister


class CashRegisterForm(forms.ModelForm):
    class Meta:
        model = CashRegister
        fields = ["name", "active", "terminal"]
        labels = {
            "name": "Nombre de caja",
            "active": "Activa",
            "terminal": "Terminal (vacío: compartida)",
        }
