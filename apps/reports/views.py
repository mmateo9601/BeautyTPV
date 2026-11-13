import csv
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.permissions import role_required
from apps.audit.services import record
from apps.pos.models import Payment, Sale


@role_required("MANAGER")
def index(request):
    today = timezone.localdate()
    try:
        start = date.fromisoformat(request.GET.get("start", str(today)))
        end = date.fromisoformat(request.GET.get("end", str(today)))
        if start > end:
            raise ValueError
    except ValueError:
        return HttpResponse("Fechas no válidas.", status=400)
    since = timezone.make_aware(datetime.combine(start, time.min))
    until = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
    rows = (
        Sale.objects.filter(created_at__gte=since, created_at__lt=until)
        .select_related("created_by", "ticket__station")
        .prefetch_related("ticket__lines", "payments")
    )
    payments = list(
        Payment.objects.filter(sale__in=rows).values("method").annotate(total=Sum("amount"))
    )
    totals = {
        "sales": rows.count(),
        "total": rows.aggregate(total=Sum("total"))["total"] or Decimal("0"),
        "refunds": Decimal("0"),
    }
    tax = defaultdict(
        lambda: {"net_total": Decimal("0"), "tax_total": Decimal("0"), "total": Decimal("0")}
    )
    employees = defaultdict(lambda: Decimal("0"))
    items = defaultdict(lambda: Decimal("0"))
    for sale in rows:
        employees[sale.created_by.username] += sale.total
        for line in sale.ticket.lines.all():
            tax[line.tax_rate]["net_total"] += line.net_total
            tax[line.tax_rate]["tax_total"] += line.tax_total
            tax[line.tax_rate]["total"] += line.total
            items[line.description] += line.total
    from apps.billing.models import InvoiceLine, Refund

    refunds = Refund.objects.filter(invoice__issued_at__gte=since, invoice__issued_at__lt=until)
    totals["refunds"] = refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    totals["net"] = totals["total"] - totals["refunds"]
    methods = {row["method"]: row["total"] for row in payments}
    for refund in refunds.select_related("invoice__rectifies__created_by"):
        methods[refund.method] = methods.get(refund.method, Decimal("0")) - refund.amount
        original = refund.invoice.rectifies
        if original:
            employees[original.created_by.username] -= refund.amount
    payments = [{"method": method, "total": total} for method, total in sorted(methods.items())]
    for line in InvoiceLine.objects.filter(invoice__refund__in=refunds):
        tax[line.tax_rate]["net_total"] += line.net_total
        tax[line.tax_rate]["tax_total"] += line.tax_total
        tax[line.tax_rate]["total"] += line.total
        items[line.description] += line.total
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
                    row.created_at.isoformat(),
                    "'" + row.created_by.username
                    if row.created_by.username.startswith(("=", "+", "-", "@", "\t", "\r"))
                    else row.created_by.username,
                    row.total,
                ]
            )
        writer.writerow(["Devoluciones", "", "", totals["refunds"]])
        writer.writerow(["Neto", "", "", totals["net"]])
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
        },
    )
