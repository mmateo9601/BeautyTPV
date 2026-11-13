"""Authenticated terminal-scoped transport. No client-supplied raw bytes or device targets."""

import base64
import json
import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.audit.services import record
from apps.core.guards import require_operational
from apps.core.models import Terminal

from .models import HardwareEvent, PrintJob


def authenticated_terminal(request, terminal_pk):
    terminal = Terminal.objects.filter(pk=terminal_pk, active=True).first()
    authorization = request.headers.get("Authorization", "")
    token = authorization[7:] if authorization.startswith("Bearer ") else ""
    if terminal is None or not terminal.check_bridge_token(token):
        return None
    Terminal.objects.filter(pk=terminal.pk).update(last_seen_at=timezone.now())
    return terminal


@csrf_exempt
@require_POST
def claim(request, terminal_pk):
    terminal = authenticated_terminal(request, terminal_pk)
    if terminal is None:
        return JsonResponse({"error": "Bridge no autorizado."}, status=403)
    try:
        require_operational()
    except ValidationError:
        return JsonResponse({"error": "Impresion retenida tras restauracion."}, status=503)
    now = timezone.now()
    with transaction.atomic():
        expired = PrintJob.objects.filter(
            printer__terminal=terminal, status="SENDING", lease_until__lt=now
        )
        for job in expired:
            if expired.filter(pk=job.pk).update(
                status="UNKNOWN",
                lease_until=None,
                last_error="Agente interrumpido: entrega incierta",
            ):
                HardwareEvent.objects.create(
                    job=job,
                    printer=job.printer,
                    action="UNKNOWN",
                    message="Lease expirada; no reenviar",
                )
        job = (
            PrintJob.objects.filter(
                printer__terminal=terminal, printer__enabled=True, status="PENDING"
            )
            .select_related("printer")
            .first()
        )
        if job is None:
            return JsonResponse({}, status=204)
        token = uuid.uuid4().hex
        lease = now + timedelta(minutes=2)
        if not PrintJob.objects.filter(pk=job.pk, status="PENDING").update(
            status="SENDING", attempts=F("attempts") + 1, lease_until=lease, lease_token=token
        ):
            return JsonResponse({}, status=204)
        printer = job.printer
        try:
            printer.full_clean()
        except ValidationError:
            PrintJob.objects.filter(pk=job.pk).update(
                status="FAILED",
                lease_until=None,
                last_error="Configuracion de dispositivo no valida",
            )
            return JsonResponse({"error": "Configuracion de dispositivo no valida."}, status=409)
        HardwareEvent.objects.create(job=job, printer=printer, action="CLAIMED")
        record(None, "hardware.bridge_claim", target=str(job.pk))
        return JsonResponse(
            {
                "job_id": job.pk,
                "lease_token": token,
                "lease_until": lease.isoformat(),
                "payload": base64.b64encode(bytes(job.payload)).decode("ascii"),
                "printer": {
                    field: getattr(printer, field)
                    for field in [
                        "connection_type",
                        "address",
                        "port",
                        "usb_vendor",
                        "usb_product",
                        "usb_endpoint",
                    ]
                },
            }
        )


@csrf_exempt
@require_POST
def acknowledge(request, terminal_pk, job_pk):
    terminal = authenticated_terminal(request, terminal_pk)
    if terminal is None:
        return JsonResponse({"error": "Bridge no autorizado."}, status=403)
    try:
        data = json.loads(request.body)
        state, token = data["status"], data["lease_token"]
        if state not in ("DONE", "FAILED", "UNKNOWN") or not isinstance(token, str):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "Acuse no valido."}, status=400)
    now = timezone.now()
    with transaction.atomic():
        job = PrintJob.objects.filter(pk=job_pk, printer__terminal=terminal).first()
        if job is None or not token or not constant_time_compare(job.lease_token, token):
            return JsonResponse({"error": "Trabajo o lease no autorizados."}, status=403)
        if job.status == state and job.status != "SENDING":
            return JsonResponse({"status": state, "duplicate_ack": True})
        if job.status != "SENDING" or not job.lease_until or job.lease_until <= now:
            if job.status == "SENDING":
                PrintJob.objects.filter(pk=job.pk, status="SENDING").update(
                    status="UNKNOWN",
                    lease_until=None,
                    last_error="Acuse despues de expiracion: revisar entrega",
                )
            return JsonResponse({"error": "Lease expirada o estado ya conciliado."}, status=409)
        PrintJob.objects.filter(pk=job.pk, status="SENDING", lease_token=token).update(
            status=state,
            lease_until=None,
            sent_at=now if state == "DONE" else None,
            last_error=""
            if state == "DONE"
            else "Agente: fallo previo al envio"
            if state == "FAILED"
            else "Agente: entrega incierta",
        )
        HardwareEvent.objects.create(job=job, printer=job.printer, action=state)
        record(None, "hardware.bridge_ack", target=str(job.pk), metadata={"status": state})
    return JsonResponse({"status": state})
