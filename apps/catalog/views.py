from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.audit.services import record

from .forms import CatalogItemForm, CategoryForm
from .models import CatalogItem, Category


@role_required("ADMIN")
def index(request):
    items = CatalogItem.objects.select_related("category").all()
    if request.GET.get("q"):
        items = items.filter(name__icontains=request.GET["q"])
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
        item = form.save()
        record(request.user, "catalog.save", obj=item)
        return redirect("catalog:index")
    return render(request, "catalog/form.html", {"form": form, "item": item})


@role_required("ADMIN")
def category(request, pk=None):
    selected = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, instance=selected)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        record(request.user, "catalog.category", obj=obj)
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
        with transaction.atomic():
            selected.delete()
            record(request.user, "catalog.category.deleted", target=str(pk))
    except ProtectedError:
        return HttpResponse(
            "La categoria tiene articulos. Reasignelos antes de eliminarla.", status=400
        )
    return redirect("catalog:category")
