from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.core.http import form_pk

from . import services
from .forms import CatalogItemForm, CategoryForm
from .models import CatalogItem, Category


@role_required("ADMIN")
def index(request):
    items = CatalogItem.objects.select_related("category").all()
    if request.GET.get("q"):
        items = items.filter(name__icontains=request.GET["q"])
    if request.GET.get("kind") in CatalogItem.Kind.values:
        items = items.filter(kind=request.GET["kind"])
    if request.GET.get("active") in ("yes", "no"):
        items = items.filter(active=request.GET["active"] == "yes")
    if request.GET.get("category"):
        try:
            items = items.filter(category_id=form_pk(request.GET["category"]))
        except ValidationError as error:
            return HttpResponse("; ".join(error.messages), status=400)
    return render(
        request,
        "catalog/index.html",
        {"items": items, "categories": Category.objects.all(), "form": CatalogItemForm()},
    )


@role_required("ADMIN")
def edit(request, pk=None):
    item = get_object_or_404(CatalogItem, pk=pk) if pk else None
    form = CatalogItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        try:
            services.save_catalog_item(request.user, form.save(commit=False))
            messages.success(request, "Artículo guardado.")
        except ValidationError as error:
            form.add_error(None, error)
            return render(request, "catalog/form.html", {"form": form, "item": item}, status=400)
        return redirect("catalog:index")
    return render(request, "catalog/form.html", {"form": form, "item": item})


@role_required("ADMIN")
def category(request, pk=None):
    selected = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, instance=selected)
    if request.method == "POST" and form.is_valid():
        services.save_category(request.user, form.save(commit=False))
        messages.success(request, "Categoría guardada.")
        return redirect("catalog:category")
    return render(
        request,
        "catalog/categories.html",
        {
            "form": form,
            "categories": Category.objects.all(),
            "selected": selected,
        },
        status=400 if request.method == "POST" else 200,
    )


@require_POST
@role_required("ADMIN")
def delete_category(request, pk):
    selected = get_object_or_404(Category, pk=pk)
    try:
        services.delete_category(request.user, selected)
        messages.success(request, "Categoría eliminada.")
    except ProtectedError:
        return HttpResponse(
            "La categoria tiene articulos. Reasignelos antes de eliminarla.", status=400
        )
    return redirect("catalog:category")
