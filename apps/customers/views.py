from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import role_required
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
