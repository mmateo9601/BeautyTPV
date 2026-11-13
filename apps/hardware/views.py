from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.billing.models import Invoice

from .models import Printer, PrintJob
from .services import enqueue_invoice, enqueue_test, retry_job


@require_POST
@role_required("EMPLOYEE")
def reprint(request, pk):
    invoices = Invoice.objects.all()
    if request.user.role == "EMPLOYEE":
        invoices = invoices.filter(created_by=request.user)
    invoice = get_object_or_404(invoices, pk=pk)
    enqueue_invoice(invoice, request.user, copy=True)
    messages.success(request, "Copia en cola; el cajón no se abrirá.")
    return redirect("billing:detail", pk=pk)


@require_POST
@role_required("SUPERADMIN", elevated=True)
def test_printer(request, pk):
    enqueue_test(
        get_object_or_404(Printer, pk=pk), request.user, drawer=request.POST.get("drawer") == "1"
    )
    messages.success(request, "Prueba enviada a la cola.")
    return redirect("support:index")


@require_POST
@role_required("SUPERADMIN", elevated=True)
def retry(request, pk):
    from django.core.exceptions import ValidationError

    try:
        printer = (
            get_object_or_404(Printer, pk=request.POST["printer_id"], enabled=True)
            if request.POST.get("printer_id")
            else None
        )
        retry_job(get_object_or_404(PrintJob, pk=pk), request.user, printer=printer)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Trabajo preparado para reintento seguro.")
    return redirect("support:index")
