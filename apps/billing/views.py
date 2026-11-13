from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import require_role
from apps.audit.services import record
from apps.verifactu.protocol import qr_url

from .models import Invoice
from .services import rectify_invoice, render_pdf


@login_required
def invoice_list(request):
    require_role(request.user, "EMPLOYEE")
    invoices = Invoice.objects.select_related("sale", "created_by").all()
    if request.user.role == "EMPLOYEE":
        invoices = invoices.filter(created_by=request.user)
    return render(request, "billing/list.html", {"invoices": invoices[:200]})


def _invoice(request, pk):
    require_role(request.user, "EMPLOYEE")
    query = Invoice.objects.all()
    if request.user.role == "EMPLOYEE":
        query = query.filter(created_by=request.user)
    invoice = get_object_or_404(query, pk=pk)
    record(request.user, "invoice.view", invoice.full_number)
    return invoice


@login_required
def invoice_detail(request, pk):
    invoice = _invoice(request, pk)
    from apps.cash.models import CashSession

    return render(
        request,
        "billing/detail.html",
        {
            "invoice": invoice,
            "qr_url": qr_url(invoice),
            "records": invoice.fiscal_records.select_related("outbox"),
            "lines": invoice.lines.all(),
            "cash_sessions": CashSession.objects.filter(closed_at__isnull=True),
        },
    )


@login_required
def invoice_pdf(request, pk):
    invoice = _invoice(request, pk)
    response = HttpResponse(render_pdf(invoice), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.full_number}.pdf"'
    return response


@login_required
@require_POST
def rectify(request, pk):
    invoice = _invoice(request, pk)
    try:
        from apps.cash.models import CashSession

        selected = request.POST.get("cash_session", "").strip()
        if selected and (not selected.isascii() or not selected.isdigit() or len(selected) > 18):
            raise ValidationError("Turno de caja no valido.")
        session = CashSession.objects.filter(pk=selected or None, closed_at__isnull=True).first()
        result = rectify_invoice(
            invoice,
            request.user,
            request.POST.get("reason", ""),
            request.POST.get("method", "CARD"),
            session,
            request.POST.get("reference", ""),
        )
        return redirect("billing:detail", pk=result.pk)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("billing:detail", pk=pk)


@login_required
@require_POST
def reprint(request, pk):
    invoice = _invoice(request, pk)
    from apps.hardware.services import enqueue_invoice

    enqueue_invoice(invoice, request.user, copy=True)
    messages.success(request, "Copia enviada a cola de impresión.")
    return redirect("billing:detail", pk=pk)
