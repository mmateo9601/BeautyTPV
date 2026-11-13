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
        ]
