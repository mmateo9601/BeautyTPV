from django import forms

from .models import CatalogItem, Category


class CatalogItemForm(forms.ModelForm):
    class Meta:
        model = CatalogItem
        fields = ["kind", "name", "category", "price", "tax_rate", "active"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
