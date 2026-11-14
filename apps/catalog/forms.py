from django import forms

from .models import CatalogItem, Category


class CatalogItemForm(forms.ModelForm):
    class Meta:
        model = CatalogItem
        labels = {
            "kind": "Tipo",
            "name": "Nombre",
            "category": "Categoría",
            "price": "Precio IVA incluido",
            "tax_rate": "IVA (%)",
            "active": "Activo",
            "sort_order": "Orden",
        }
        fields = ["kind", "name", "category", "price", "tax_rate", "active", "sort_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sort_order"].required = False

    def clean_sort_order(self):
        return self.cleaned_data.get("sort_order") or 0


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        labels = {"name": "Nombre", "sort_order": "Orden", "visible_in_pos": "Visible en TPV"}
        fields = ["name", "sort_order", "visible_in_pos"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sort_order"].required = False
        # Older category forms did not submit visibility; preserve the existing value.
        if self.is_bound and "visible_in_pos" not in self.data and "sort_order" not in self.data:
            self.data = self.data.copy()
            self.data["visible_in_pos"] = (
                "on" if not self.instance.pk or self.instance.visible_in_pos else ""
            )

    def clean_sort_order(self):
        return self.cleaned_data.get("sort_order") or 0
