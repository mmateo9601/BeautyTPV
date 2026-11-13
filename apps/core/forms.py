from django import forms

from .models import CompanySettings


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
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
