from django import forms

from .models import Section, Station


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ["name", "sort_order"]


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ["section", "code", "name", "active"]
