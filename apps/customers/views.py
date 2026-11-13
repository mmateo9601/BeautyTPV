import csv

from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import require_elevated, require_role, role_required
from apps.audit.services import record
from apps.pos.models import Sale

from .forms import CustomerForm
from .models import Customer


@role_required("EMPLOYEE")
def index(request):
    query = request.GET.get("q", "")
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(phone__icontains=query))
    if request.GET.get("format") == "csv":
        require_role(request.user, "ADMIN")
        require_elevated(request)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="clientes.csv"'
        writer = csv.writer(response)
        writer.writerow(["Nombre", "Telefono", "Email", "NIF", "Domicilio"])
        for customer in customers:
            values = [
                customer.name,
                customer.phone,
                customer.email,
                customer.tax_id,
                customer.address,
            ]
            writer.writerow(
                [
                    "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
                    for value in values
                ]
            )
        record(request.user, "customer.export")
        return response
    record(request.user, "customer.list")
    return render(
        request,
        "customers/index.html",
        {"customers": customers[:200], "form": CustomerForm(), "query": query},
    )


@role_required("EMPLOYEE")
def edit(request, pk=None):
    customer = get_object_or_404(Customer, pk=pk) if pk else None
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        record(request.user, "customer.save", obj=customer)
        return redirect("customers:detail", pk=customer.pk)
    record(request.user, "customer.access", obj=customer)
    return render(request, "customers/form.html", {"form": form, "customer": customer})


@role_required("EMPLOYEE")
def detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    record(request.user, "customer.history", obj=customer)
    return render(
        request,
        "customers/detail.html",
        {
            "customer": customer,
            "sales": Sale.objects.filter(ticket__customer=customer)
            .select_related("ticket", "created_by")
            .order_by("-created_at"),
        },
    )


@require_POST
@role_required("ADMIN", elevated=True)
def delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    try:
        with transaction.atomic():
            customer.delete()
            record(request.user, "customer.deleted", target=str(pk))
    except ProtectedError:
        return HttpResponse("Cliente con historial protegido: no puede eliminarse.", status=400)
    return redirect("customers:index")
