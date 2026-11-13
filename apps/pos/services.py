import hashlib
import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from apps.accounts.permissions import require_role
from apps.audit.services import record

from .models import OpenTicket, Payment, Sale, TicketLine, money


class TicketConflict(ValidationError):
    pass


def decimal_value(value, label="importe"):
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{label} no válido.")


def _lock_ticket(ticket, expected_version=None):
    current = OpenTicket.objects.get(pk=ticket.pk)
    if current.status != "OPEN":
        raise ValidationError("La cuenta ya no está abierta.")
    version = current.version if expected_version is None else int(expected_version)
    if not OpenTicket.objects.filter(pk=current.pk, status="OPEN", version=version).update(
        version=F("version") + 1
    ):
        raise TicketConflict("Otra terminal modificó la cuenta. Recargue.")
    current.version = version + 1
    return current


@transaction.atomic
def open_ticket(station, actor):
    require_role(actor, "EMPLOYEE")
    if not station.active:
        raise ValidationError("Puesto no disponible.")
    ticket = OpenTicket.objects.filter(
        station=station, status__in=["OPEN", "PAYMENT_PENDING"]
    ).first()
    if ticket:
        return ticket
    ticket = OpenTicket.objects.create(station=station, created_by=actor)
    record(actor, "ticket.open", obj=ticket)
    return ticket


@transaction.atomic
def add_line(
    ticket, item, actor, quantity=Decimal("1"), discount_percent=Decimal("0"), expected_version=None
):
    require_role(actor, "EMPLOYEE")
    ticket = _lock_ticket(ticket, expected_version)
    if not item.active:
        raise ValidationError("Artículo inactivo.")
    quantity = decimal_value(quantity, "Cantidad")
    discount_percent = decimal_value(discount_percent, "Descuento")
    if quantity <= 0 or quantity.as_tuple().exponent < -3 or not 0 <= discount_percent <= 100:
        raise ValidationError("Cantidad o descuento no válido.")
    if discount_percent:
        require_role(actor, "MANAGER")
    line = TicketLine(
        ticket=ticket,
        item=item,
        description=item.name,
        quantity=quantity,
        unit_price=item.price,
        tax_rate=item.tax_rate,
        discount_percent=discount_percent,
    )
    line.full_clean()
    line.save()
    record(actor, "ticket.line.add", obj=line)
    return line


@transaction.atomic
def update_line(line, actor, quantity=None, discount_percent=None, expected_version=None):
    require_role(actor, "EMPLOYEE")
    ticket = _lock_ticket(line.ticket, expected_version)
    line = TicketLine.objects.get(pk=line.pk)
    line.ticket = ticket
    if quantity is not None:
        qty = decimal_value(quantity, "Cantidad")
        if qty < line.quantity:
            require_role(actor, "MANAGER")
        line.quantity = qty
    if discount_percent is not None:
        discount = decimal_value(discount_percent, "Descuento")
        if discount != line.discount_percent:
            require_role(actor, "MANAGER")
        line.discount_percent = discount
    line.full_clean()
    line.save()
    record(actor, "ticket.line.update", obj=line)
    return line


@transaction.atomic
def remove_line(line, actor, expected_version=None):
    require_role(actor, "MANAGER")
    _lock_ticket(line.ticket, expected_version)
    record(actor, "ticket.line.remove", obj=line)
    line.delete()


@transaction.atomic
def set_customer(ticket, customer, actor, expected_version=None):
    require_role(actor, "EMPLOYEE")
    ticket = _lock_ticket(ticket, expected_version)
    OpenTicket.objects.filter(pk=ticket.pk).update(customer=customer)
    record(actor, "ticket.customer", obj=ticket)
    return ticket


@transaction.atomic
def cancel_ticket(ticket, actor, expected_version=None):
    require_role(actor, "MANAGER")
    ticket = _lock_ticket(ticket, expected_version)
    OpenTicket.objects.filter(pk=ticket.pk).update(status="CANCELLED")
    record(actor, "ticket.cancel", obj=ticket)
    return ticket


@transaction.atomic
def checkout(ticket, actor, payments, idempotency_key, cash_session=None, expected_version=None):
    from apps.core.guards import require_operational

    require_operational()
    require_role(actor, "EMPLOYEE")
    if not idempotency_key or len(str(idempotency_key)) > 100:
        raise ValidationError("Clave de cobro no válida.")
    normalized = []
    for payment in payments:
        method = payment.get("method")
        amount = decimal_value(payment.get("amount"))
        received = (
            decimal_value(payment["received"]) if payment.get("received") is not None else None
        )
        reference = str(payment.get("reference", "")).strip()
        if method not in ["CASH", "CARD"] or amount <= 0 or amount != money(amount):
            raise ValidationError("Pago no válido.")
        if method == "CARD" and not reference:
            raise ValidationError("Confirme la referencia del datáfono externo.")
        if len(reference) > 100:
            raise ValidationError("Referencia demasiado larga.")
        if received is not None and (received < amount or received != money(received)):
            raise ValidationError("Efectivo recibido insuficiente o no válido.")
        normalized.append(
            {
                "method": method,
                "amount": str(amount),
                "received": str(received) if received is not None else None,
                "reference": reference,
            }
        )
    payload = {
        "ticket": ticket.pk,
        "payments": normalized,
        "cash_session": getattr(cash_session, "pk", None),
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    existing = Sale.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise ValidationError("Clave de cobro reutilizada con otros datos.")
        return existing
    ticket = _lock_ticket(ticket, expected_version)
    lines = list(ticket.lines.all())
    total = sum((line.total for line in lines), Decimal("0"))
    if total <= 0 or sum((Decimal(p["amount"]) for p in normalized), Decimal("0")) != total:
        raise ValidationError("Los pagos deben sumar exactamente el total positivo.")
    cash_amount = sum(
        (Decimal(p["amount"]) for p in normalized if p["method"] == "CASH"), Decimal("0")
    )
    if cash_amount:
        from apps.cash.models import CashSession

        if (
            cash_session is None
            or not CashSession.objects.filter(pk=cash_session.pk, closed_at__isnull=True).exists()
        ):
            raise ValidationError("Abra una caja para el efectivo.")
    sale = Sale.objects.create(
        ticket=ticket,
        total=total,
        created_by=actor,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
    )
    for p in normalized:
        Payment.objects.create(
            sale=sale,
            method=p["method"],
            amount=Decimal(p["amount"]),
            received=Decimal(p["received"]) if p["received"] else None,
            reference=p["reference"],
            cash_session=cash_session if p["method"] == "CASH" else None,
        )
    from apps.billing.services import issue_invoice
    from apps.hardware.services import enqueue_invoice

    invoice = issue_invoice(sale, actor)
    enqueue_invoice(invoice, actor, open_drawer=cash_amount > 0)
    OpenTicket.objects.filter(pk=ticket.pk, status="OPEN", version=ticket.version).update(
        status="CLOSED"
    )
    record(actor, "sale.checkout", obj=sale, metadata={"total": str(total)})
    return sale
