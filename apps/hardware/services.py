from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.audit.services import record

from .drivers import DeliveryUnknown, DriverUnavailable, send
from .escpos import render_receipt, render_test
from .models import HardwareEvent, Printer, PrintJob


@transaction.atomic
def enqueue_invoice(invoice, actor, open_drawer=False, copy=False):
    from apps.core.guards import require_operational

    require_operational()
    require_role(actor, "EMPLOYEE")
    if copy:
        if actor.role == "EMPLOYEE" and invoice.created_by_id != actor.pk:
            raise PermissionDenied("Solo puede reimprimir sus propias facturas.")
        open_drawer = False
    elif open_drawer:
        if (
            not invoice.sale_id
            or not invoice.sale.payments.filter(method="CASH", amount__gt=0).exists()
        ):
            raise ValidationError("El cajón requiere un pago en efectivo.")
    if not copy:
        existing = PrintJob.objects.filter(invoice=invoice, kind="RECEIPT").first()
        if existing:
            return existing
    terminal_id = None
    if invoice.sale_id:
        terminal_id = getattr(invoice.sale.ticket, "terminal_id", None)
    printer = None
    if terminal_id:
        printer = (
            Printer.objects.filter(enabled=True, terminal_id=terminal_id).order_by("pk").first()
        )
    if printer is None:
        printer = Printer.objects.filter(enabled=True, terminal__isnull=True).order_by("pk").first()
    configuration_error = ""
    if printer:
        try:
            printer.full_clean()
        except ValidationError:
            # An invalid device must not roll back an otherwise valid financial sale.
            printer = None
            configuration_error = (
                "Configuracion de impresora invalida; asigne un dispositivo valido."
            )
    if printer and not printer.drawer_enabled:
        open_drawer = False
    payload = render_receipt(
        invoice,
        copy=copy,
        open_drawer=open_drawer,
        encoding=printer.encoding if printer else "cp858",
        codepage=printer.codepage if printer else 19,
        cut_paper=printer.cut_paper if printer else True,
    )
    job = PrintJob.objects.create(
        invoice=invoice,
        printer=printer,
        kind="COPY" if copy else "RECEIPT",
        payload=payload,
        encoding=printer.encoding if printer else "cp858",
        codepage=printer.codepage if printer else 19,
        last_error=configuration_error,
        open_drawer=open_drawer,
        requested_by=actor,
    )
    HardwareEvent.objects.create(job=job, printer=printer, action="ENQUEUED")
    record(actor, "hardware.enqueued", obj=job)
    return job


@transaction.atomic
def enqueue_test(printer, actor, drawer=False):
    from apps.core.guards import require_operational

    require_operational()
    require_role(actor, "SUPERADMIN")
    printer = Printer.objects.get(pk=printer.pk)
    if not printer.enabled:
        raise ValidationError("Dispositivo deshabilitado")
    printer.full_clean()
    if drawer and not printer.drawer_enabled:
        raise ValidationError("El cajon esta deshabilitado en la configuracion del dispositivo.")
    job = PrintJob.objects.create(
        printer=printer,
        kind="DRAWER" if drawer else "TEST",
        requested_by=actor,
        open_drawer=drawer,
        payload=render_test(
            printer.encoding, printer.codepage, drawer, cut_paper=printer.cut_paper
        ),
        encoding=printer.encoding,
        codepage=printer.codepage,
    )
    record(actor, "hardware.test_drawer" if drawer else "hardware.test", obj=job)
    return job


@transaction.atomic
def retry_job(job, actor, printer=None):
    from apps.core.guards import require_operational

    require_operational()
    require_role(actor, "SUPERADMIN")
    current = PrintJob.objects.get(pk=job.pk)
    if current.status not in ["FAILED", "PENDING"]:
        raise ValidationError(
            "Solo reintentar fallos previos al envío. Entrega incierta requiere copia explícita sin cajón."
        )
    current.status = "PENDING"
    current.last_error = ""
    if printer is not None:
        printer = Printer.objects.get(pk=printer.pk)
        if not printer.enabled:
            raise ValidationError("Dispositivo deshabilitado")
        printer.full_clean()
        if printer.encoding != current.encoding or printer.codepage != current.codepage:
            raise ValidationError(
                "Codificacion distinta del trabajo original: emita copia en el nuevo dispositivo."
            )
        current.printer = printer
    current.save(update_fields=["status", "last_error", "printer"])
    record(actor, "hardware.retry", obj=current)
    return current


@transaction.atomic
def save_printer(printer, actor):
    """Protected configuration entry point; existing print intentions remain unchanged."""
    require_role(actor, "SUPERADMIN")
    printer.full_clean()
    printer.save()
    record(actor, "device.saved", obj=printer)
    return printer


def recover_expired():
    from apps.core.guards import require_operational

    require_operational()
    # Crash may have happened after the physical write. Never resend automatically.
    return PrintJob.objects.filter(status="SENDING", lease_until__lt=timezone.now()).update(
        status="UNKNOWN", last_error="Worker interrumpido: entrega incierta", lease_until=None
    )


def process_job(job_id):
    from apps.core.guards import require_operational

    require_operational()
    now = timezone.now()
    with transaction.atomic():
        changed = PrintJob.objects.filter(
            pk=job_id, status="PENDING", printer__enabled=True, printer__terminal__isnull=True
        ).update(
            status="SENDING", attempts=F("attempts") + 1, lease_until=now + timedelta(seconds=60)
        )
        if not changed:
            return False
        job = PrintJob.objects.select_related("printer").get(pk=job_id)
    try:
        send(job.printer, job.payload)
        status, error = "DONE", ""
    except DriverUnavailable:
        status, error = "FAILED", "Dispositivo no disponible antes del envío"
    except DeliveryUnknown:
        status, error = "UNKNOWN", "Entrega incierta; no reintentar automáticamente"
    except Exception:
        status, error = "UNKNOWN", "Error de driver; revisar entrega antes de reimprimir"
    with transaction.atomic():
        changed = PrintJob.objects.filter(
            pk=job.pk, status="SENDING", lease_until=job.lease_until
        ).update(
            status=status,
            last_error=error,
            lease_until=None,
            sent_at=timezone.now() if status == "DONE" else None,
        )
        if not changed:
            status, error = (
                "UNKNOWN",
                "Estado cambiado durante entrega: requiere conciliacion manual.",
            )
        HardwareEvent.objects.create(job=job, printer=job.printer, action=status, message=error)
        record(None, "hardware.processed", obj=job, metadata={"status": status})
    return status == "DONE"
