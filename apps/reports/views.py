import csv
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.audit.services import record
from apps.billing.models import Invoice, InvoiceLine, Refund
from apps.cash.models import CashRegister, CashSession
from apps.catalog.models import CatalogItem
from apps.core.http import form_pk
from apps.core.models import CompanySettings
from apps.pos.models import OpenTicket, Payment, Sale


def _sum(queryset, field):
    return queryset.aggregate(total=Sum(field))["total"] or Decimal("0.00")


def _filters(request):
    selected = {
        key: request.GET.get(key, "") for key in ("register_id", "method", "employee_id", "item_id")
    }
    for key in ("register_id", "employee_id", "item_id"):
        if selected[key]:
            form_pk(selected[key])
    if selected["method"] not in ("", "CASH", "CARD"):
        raise ValidationError("Metodo de pago no valido.")
    return selected


def _period(request):
    zone = ZoneInfo(CompanySettings.load().timezone)
    today = timezone.now().astimezone(zone).date()
    start = date.fromisoformat(request.GET.get("start", str(today)))
    end = date.fromisoformat(request.GET.get("end", str(today)))
    if start > end or end == date.max:
        raise ValueError
    since = datetime.combine(start, time.min, tzinfo=zone)
    until = datetime.combine(end + timedelta(days=1), time.min, tzinfo=zone)
    return start, end, since, until, zone


def _select_operations(rows, refunds, selected):
    if selected["register_id"]:
        rows = rows.filter(payments__cash_session__register_id=selected["register_id"])
        refunds = refunds.filter(cash_session__register_id=selected["register_id"])
    if selected["method"]:
        rows = rows.filter(payments__method=selected["method"])
        refunds = refunds.filter(method=selected["method"])
    if selected["employee_id"]:
        rows = rows.filter(created_by_id=selected["employee_id"])
        refunds = refunds.filter(invoice__rectifies__created_by_id=selected["employee_id"])
    if selected["item_id"]:
        rows = rows.filter(ticket__lines__item_id=selected["item_id"])
        refunds = refunds.filter(
            invoice__rectifies__sale__ticket__lines__item_id=selected["item_id"]
        )
    return rows.distinct(), refunds.distinct()


def _safe_csv(value):
    text = str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


@role_required("MANAGER")
def index(request):
    try:
        selected = _filters(request)
        start, end, since, until, zone = _period(request)
    except (ValidationError, ValueError, OverflowError, ZoneInfoNotFoundError):
        return HttpResponse("Fechas o filtros no validos.", status=400)
    rows, refunds = _select_operations(
        Sale.objects.filter(created_at__gte=since, created_at__lt=until),
        Refund.objects.filter(invoice__issued_at__gte=since, invoice__issued_at__lt=until),
        selected,
    )
    rows = (
        rows.select_related("created_by", "ticket__station", "invoice")
        .prefetch_related("payments")
        .order_by("-created_at")
    )
    refunds = refunds.select_related("invoice__rectifies__created_by", "cash_session__register")
    totals = {
        "sales": rows.count(),
        "total": _sum(rows, "total"),
        "refunds": _sum(refunds, "amount"),
    }
    totals["net"] = totals["total"] - totals["refunds"]
    tax = defaultdict(
        lambda: {"net_total": Decimal("0"), "tax_total": Decimal("0"), "total": Decimal("0")}
    )
    employees = defaultdict(lambda: Decimal("0"))
    items = defaultdict(lambda: Decimal("0"))
    methods = defaultdict(lambda: Decimal("0"))
    for payment in Payment.objects.filter(sale__in=rows):
        methods[payment.method] += payment.amount
    for sale in rows:
        employees[sale.created_by.username] += sale.total
    # The emitted fiscal snapshots are the reporting source, never mutable catalogue prices.
    lines = InvoiceLine.objects.filter(Q(invoice__sale__in=rows) | Q(invoice__refund__in=refunds))
    for line in lines:
        tax[line.tax_rate]["net_total"] += line.net_total
        tax[line.tax_rate]["tax_total"] += line.tax_total
        tax[line.tax_rate]["total"] += line.total
        items[line.description] += line.total
    for refund in refunds:
        methods[refund.method] -= refund.amount
        if refund.invoice.rectifies_id:
            employees[refund.invoice.rectifies.created_by.username] -= refund.amount
    payments = [{"method": method, "total": total} for method, total in sorted(methods.items())]
    cancellations = OpenTicket.objects.filter(
        status="CANCELLED", cancelled_at__gte=since, cancelled_at__lt=until
    )
    if selected["employee_id"]:
        cancellations = cancellations.filter(created_by_id=selected["employee_id"])
    if selected["item_id"]:
        cancellations = cancellations.filter(lines__item_id=selected["item_id"])
    if selected["register_id"] or selected["method"]:
        cancellations = (
            cancellations.none()
        )  # Uncharged accounts have no payment method or cash register.
    cancellations = cancellations.select_related("created_by", "cancelled_by", "station").distinct()
    invoices = Invoice.objects.filter(Q(sale__in=rows) | Q(refund__in=refunds)).select_related(
        "created_by", "rectifies"
    )
    sessions = (
        CashSession.objects.filter(opened_at__lt=until)
        .filter(Q(closed_at__gte=since) | Q(closed_at__isnull=True))
        .select_related("register", "opened_by", "closed_by")
    )
    if selected["register_id"]:
        sessions = sessions.filter(register_id=selected["register_id"])
    totals["cancelled"] = cancellations.count()
    totals["invoices"] = invoices.count()
    if request.GET.get("format") == "csv":
        record(request.user, "report.export")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="ventas.csv"'
        writer = csv.writer(response)
        writer.writerow(["Venta", "Fecha", "Empleado", "Total"])
        for row in rows:
            writer.writerow(
                [
                    row.pk,
                    row.created_at.astimezone(zone).isoformat(),
                    _safe_csv(row.created_by.username),
                    row.total,
                ]
            )
        writer.writerow(["Devoluciones", "", "", totals["refunds"]])
        writer.writerow(["Neto", "", "", totals["net"]])
        writer.writerow([])
        writer.writerow(["Metodo", "Neto EUR"])
        writer.writerows((row["method"], row["total"]) for row in payments)
        writer.writerow([])
        writer.writerow(["IVA", "Base", "Cuota", "Total"])
        for rate, values in sorted(tax.items()):
            writer.writerow([rate, values["net_total"], values["tax_total"], values["total"]])
        writer.writerow([])
        writer.writerow(["Concepto", "Neto EUR"])
        writer.writerows((_safe_csv(name), total) for name, total in sorted(items.items()))
        writer.writerow([])
        writer.writerow(["Empleado", "Neto EUR"])
        writer.writerows((_safe_csv(name), total) for name, total in sorted(employees.items()))
        writer.writerow([])
        writer.writerow(["Cuenta anulada", "Fecha", "Responsable"])
        for account in cancellations:
            writer.writerow(
                [
                    account.pk,
                    account.cancelled_at.astimezone(zone).isoformat(),
                    _safe_csv(account.cancelled_by.username if account.cancelled_by else ""),
                ]
            )
        return response
    record(request.user, "report.view")
    return render(
        request,
        "reports/index.html",
        {
            "totals": totals,
            "payments": payments,
            "tax_totals": [{"tax_rate": rate, **values} for rate, values in sorted(tax.items())],
            "rows": rows,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "employees": dict(employees),
            "items": dict(items),
            "refunds": refunds,
            "filters": selected,
            "registers": CashRegister.objects.all(),
            "report_employees": User.objects.all().order_by("username"),
            "catalog_items": CatalogItem.objects.all(),
            "cancellations": cancellations,
            "invoices": invoices,
            "cash_sessions": sessions,
            "undated_cancellations": OpenTicket.objects.filter(
                status="CANCELLED", cancelled_at__isnull=True
            ).count(),
        },
    )
