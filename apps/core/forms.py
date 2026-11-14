from django import forms

from .models import CompanySettings


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        labels = {
            "name": "Razón social",
            "tax_id": "NIF",
            "address": "Domicilio fiscal",
            "timezone": "Zona horaria",
            "producer_name": "Productor del software",
            "producer_tax_id": "NIF del productor",
            "installation_number": "Identificador de instalación",
            "quick_sale_enabled": "Permitir venta rápida",
            "simplified_series": "Serie simplificada",
            "full_series": "Serie completa",
            "rectification_series": "Serie rectificativa",
        }
        fields = [
            "name",
            "tax_id",
            "address",
            "timezone",
            "producer_name",
            "producer_tax_id",
            "installation_number",
            "quick_sale_enabled",
            "simplified_series",
            "full_series",
            "rectification_series",
        ]


class CommercialSettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ["trade_name", "commercial_address", "phone", "email", "ticket_footer"]


class FiscalSettingsForm(CompanySettingsForm):
    class Meta(CompanySettingsForm.Meta):
        fields = [
            field for field in CompanySettingsForm.Meta.fields if field != "quick_sale_enabled"
        ]


class PosSettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        labels = {
            "quick_sale_enabled": "Permitir venta rápida",
            "theme": "Apariencia",
            "floor_density": "Densidad del plano",
            "state_palette": "Contraste de estados",
            "default_section": "Sección inicial",
        }
        fields = [
            "quick_sale_enabled",
            "theme",
            "floor_density",
            "state_palette",
            "default_section",
        ]


class LogoForm(forms.Form):
    logo = forms.FileField(required=False, label="Logotipo PNG, JPEG o WebP (máximo 2 MiB)")
    remove_logo = forms.BooleanField(required=False, label="Retirar logotipo actual")

    def clean(self):
        values = super().clean()
        if not values.get("logo") and not values.get("remove_logo"):
            raise forms.ValidationError("Seleccione una imagen o retire el logotipo actual.")
        return values
