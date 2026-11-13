import uuid

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.cash.models import CashSession
from apps.catalog.models import CatalogItem
from apps.customers.models import Customer
from apps.layout.models import Section, Station

from . import services
from .models import OpenTicket, TicketLine


def _error(request, exc):
    return render(
        request,
        "errors/operation.html",
        {"error": "; ".join(exc.messages)},
        status=409 if isinstance(exc, services.TicketConflict) else 400,
    )


def _version(request):
    value = request.POST.get("version")
    try:
        return int(value) if value else None
    except ValueError:
        raise ValidationError("Versión no válida.")


@role_required("EMPLOYEE")
def floor(request):
    sections = list(Section.objects.prefetch_related("stations"))
    active = {
        t.station_id: t for t in OpenTicket.objects.filter(status__in=["OPEN", "PAYMENT_PENDING"])
    }
    for section in sections:
        for station in section.stations.all():
            station.active_ticket = active.get(station.pk)
    return render(request, "pos/floor.html", {"sections": sections, "tickets_by_station": active})


@require_POST
@role_required("EMPLOYEE")
def open_station(request, pk):
    try:
        ticket = services.open_ticket(get_object_or_404(Station, pk=pk), request.user)
    except ValidationError as exc:
        return _error(request, exc)
    return redirect("pos:ticket", pk=ticket.pk)


@role_required("EMPLOYEE")
def ticket(request, pk):
    account = get_object_or_404(OpenTicket.objects.select_related("station", "customer"), pk=pk)
    key = request.session.setdefault("ticket_keys", {}).setdefault(str(pk), str(uuid.uuid4()))
    request.session.modified = True
    items = CatalogItem.objects.filter(active=True)
    if request.GET.get("q"):
        items = items.filter(name__icontains=request.GET["q"])
    return render(
        request,
        "pos/ticket.html",
        {
            "ticket": account,
            "lines": account.lines.all(),
            "items": items,
            "customers": Customer.objects.all(),
            "total": account.total,
            "idempotency_key": key,
            "version": account.version,
            "cash_sessions": CashSession.objects.filter(closed_at__isnull=True).select_related(
                "register"
            ),
        },
    )


@require_POST
@role_required("EMPLOYEE")
def add_line(request, pk):
    account = get_object_or_404(OpenTicket, pk=pk)
    try:
        services.add_line(
            account,
            get_object_or_404(CatalogItem, pk=request.POST.get("item_id")),
            request.user,
            request.POST.get("quantity", "1"),
            request.POST.get("discount_percent", "0"),
            _version(request),
        )
    except ValidationError as exc:
        return _error(request, exc)
    return redirect("pos:ticket", pk=pk)


@require_POST
@role_required("EMPLOYEE")
def update_line(request, pk):
    line = get_object_or_404(TicketLine, pk=pk)
    try:
        services.update_line(
            line,
            request.user,
            request.POST.get("quantity"),
            request.POST.get("discount_percent"),
            _version(request),
        )
    except ValidationError as exc:
        return _error(request, exc)
    return redirect("pos:ticket", pk=line.ticket_id)


@require_POST
@role_required("MANAGER")
def remove_line(request, pk):
    line = get_object_or_404(TicketLine, pk=pk)
    try:
        services.remove_line(line, request.user, _version(request))
    except ValidationError as exc:
        return _error(request, exc)
    return redirect("pos:ticket", pk=line.ticket_id)


@require_POST
@role_required("MANAGER")
def cancel_ticket(request, pk):
    try:
        services.cancel_ticket(
            get_object_or_404(OpenTicket, pk=pk), request.user, _version(request)
        )
    except ValidationError as exc:
        return _error(request, exc)
    return redirect("pos:floor")


@require_POST
@role_required("EMPLOYEE")
def customer(request, pk):
    account = get_object_or_404(OpenTicket, pk=pk)
    selected = (
        get_object_or_404(Customer, pk=request.POST["customer_id"])
        if request.POST.get("customer_id")
        else None
    )
    try:
        services.set_customer(account, selected, request.user, _version(request))
    except ValidationError as exc:
        return _error(request, exc)
    return redirect("pos:ticket", pk=pk)


@require_POST
@role_required("EMPLOYEE")
def checkout(request, pk):
    account = get_object_or_404(OpenTicket, pk=pk)
    try:
        payments = []
        for method, key in [("CASH", "cash_amount"), ("CARD", "card_amount")]:
            amount = services.decimal_value(request.POST.get(key) or "0")
            if amount < 0:
                raise ValidationError("Importe negativo.")
            if amount:
                p = {"method": method, "amount": amount}
                if method == "CASH" and request.POST.get("received"):
                    p["received"] = request.POST["received"]
                if method == "CARD":
                    p["reference"] = request.POST.get("card_reference", "")
                payments.append(p)
        session = (
            get_object_or_404(CashSession, pk=request.POST["cash_session_id"])
            if request.POST.get("cash_session_id")
            else None
        )
        sale = services.checkout(
            account,
            request.user,
            payments,
            request.POST.get("idempotency_key"),
            session,
            _version(request),
        )
    except ValidationError as exc:
        return _error(request, exc)
    messages.success(
        request, "Venta registrada. La impresión y remisión fiscal se procesan en cola."
    )
    return redirect("billing:detail", pk=sale.invoice.pk)
