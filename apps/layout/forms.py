from django import forms

from .models import Section, Station


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        labels = {"name": "Nombre", "sort_order": "Orden"}
        fields = ["name", "sort_order"]


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        labels = {
            "name": "Nombre",
            "section": "Sección",
            "code": "Código",
            "active": "Activo",
            "sort_order": "Orden",
        }
        fields = ["section", "code", "name", "active", "sort_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sort_order"].required = False

    def clean_sort_order(self):
        return self.cleaned_data.get("sort_order") or 0
