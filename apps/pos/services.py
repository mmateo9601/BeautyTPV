import hashlib
import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.audit.services import record
from apps.core.guards import require_operational
from apps.core.transactions import atomic_retry

from .models import OpenTicket, Payment, Sale, TicketLine, money


class TicketConflict(ValidationError):
    pass


def decimal_value(value, label="importe"):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result.copy_abs() >= Decimal("1000000000000"):
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{label} no válido.")


def _lock_ticket(ticket, expected_version=None, allowed_states=("OPEN",)):
    current = OpenTicket.objects.get(pk=ticket.pk)
    if current.status not in allowed_states:
        raise ValidationError("La cuenta ya no está abierta.")
    try:
        version = current.version if expected_version is None else int(expected_version)
        if version < 0 or version > 2**63 - 1:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        raise ValidationError("Version no valida.") from None
    if not OpenTicket.objects.filter(
        pk=current.pk, status__in=allowed_states, version=version
    ).update(version=F("version") + 1):
        raise TicketConflict("Otra terminal modificó la cuenta. Recargue.")
    current.version = version + 1
    return current


@atomic_retry
def open_ticket(station, actor, terminal=None):
    require_role(actor, "EMPLOYEE")
    require_operational()
    from apps.layout.models import Station

    station = Station.objects.get(pk=station.pk)
    if not station.active:
        raise ValidationError("Puesto no disponible.")
    ticket = OpenTicket.objects.filter(
        station=station, status__in=["OPEN", "PAYMENT_PENDING"]
    ).first()
    if ticket:
        return ticket
    _validate_terminal(terminal)
    ticket = OpenTicket.objects.create(station=station, created_by=actor, terminal=terminal)
    record(actor, "ticket.open", obj=ticket)
    return ticket


def _validate_terminal(terminal):
    from apps.core.models import Terminal

    if terminal is not None and not Terminal.objects.filter(pk=terminal.pk, active=True).exists():
        raise ValidationError("Terminal no disponible.")


@atomic_retry
def quick_ticket(actor, terminal=None):
    from apps.core.models import CompanySettings

    require_role(actor, "EMPLOYEE")
    require_operational()
    if not CompanySettings.load().quick_sale_enabled:
        raise ValidationError("Venta rapida desactivada en la configuracion de empresa.")
    _validate_terminal(terminal)
    ticket = OpenTicket.objects.filter(
        station__isnull=True,
        created_by=actor,
        terminal=terminal,
        status__in=["OPEN", "PAYMENT_PENDING"],
    ).first()
    if ticket is None:
        ticket = OpenTicket.objects.create(created_by=actor, terminal=terminal)
        record(actor, "ticket.quick_open", obj=ticket)
    return ticket


@atomic_retry
def prepare_payment(ticket, actor, expected_version=None):
    require_role(actor, "EMPLOYEE")
    require_operational()
    ticket = _lock_ticket(ticket, expected_version)
    if ticket.total <= 0:
        raise ValidationError("La cuenta esta vacia.")
    OpenTicket.objects.filter(pk=ticket.pk).update(status="PAYMENT_PENDING")
    record(actor, "ticket.payment_pending", obj=ticket)
    return OpenTicket.objects.get(pk=ticket.pk)


@atomic_retry
def resume_ticket(ticket, actor, expected_version=None):
    require_role(actor, "EMPLOYEE")
    require_operational()
    ticket = _lock_ticket(ticket, expected_version, ("PAYMENT_PENDING",))
    OpenTicket.objects.filter(pk=ticket.pk).update(status="OPEN")
    record(actor, "ticket.payment_resumed", obj=ticket)
    return OpenTicket.objects.get(pk=ticket.pk)


@atomic_retry
def add_line(
    ticket,
    item,
    actor,
    quantity=Decimal("1"),
    discount_percent=Decimal("0"),
    expected_version=None,
    note="",
):
    require_role(actor, "EMPLOYEE")
    require_operational()
    ticket = _lock_ticket(ticket, expected_version)
    from apps.catalog.models import CatalogItem

    item = CatalogItem.objects.get(pk=item.pk)
    if not item.active or (item.category_id and not item.category.visible_in_pos):
        raise ValidationError("Artículo no disponible en TPV.")
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
        note=str(note).strip(),
    )
    line.full_clean()
    line.save()
    record(actor, "ticket.line.add", obj=line)
    return line


@atomic_retry
def update_line(
    line, actor, quantity=None, discount_percent=None, expected_version=None, note=None
):
    require_role(actor, "EMPLOYEE")
    require_operational()
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
    if note is not None:
        line.note = str(note).strip()
    line.full_clean()
    line.save()
    record(actor, "ticket.line.update", obj=line)
    return line


@atomic_retry
def remove_line(line, actor, expected_version=None):
    require_role(actor, "MANAGER")
    require_operational()
    _lock_ticket(line.ticket, expected_version)
    record(actor, "ticket.line.remove", obj=line)
    line.delete()


@atomic_retry
def set_customer(ticket, customer, actor, expected_version=None):
    require_role(actor, "EMPLOYEE")
    require_operational()
    ticket = _lock_ticket(ticket, expected_version)
    OpenTicket.objects.filter(pk=ticket.pk).update(customer=customer)
    record(actor, "ticket.customer", obj=ticket)
    return ticket


@atomic_retry
def cancel_ticket(ticket, actor, expected_version=None):
    require_role(actor, "MANAGER")
    require_operational()
    ticket = _lock_ticket(ticket, expected_version, ("OPEN", "PAYMENT_PENDING"))
    OpenTicket.objects.filter(pk=ticket.pk).update(
        status="CANCELLED", cancelled_at=timezone.now(), cancelled_by=actor
    )
    record(actor, "ticket.cancel", obj=ticket)
    return ticket


@atomic_retry
def checkout(
    ticket,
    actor,
    payments,
    idempotency_key,
    cash_session=None,
    expected_version=None,
    terminal=None,
):
    require_role(actor, "EMPLOYEE")
    require_operational()
    if not idempotency_key or len(str(idempotency_key)) > 100:
        raise ValidationError("Clave de cobro no válida.")
    if not isinstance(payments, (list, tuple)) or not payments or len(payments) > 20:
        raise ValidationError("Desglose de pagos no valido.")
    normalized = []
    for payment in payments:
        if not isinstance(payment, dict):
            raise ValidationError("Componente de pago no valido.")
        method = payment.get("method")
        amount = decimal_value(payment.get("amount"))
        received = (
            decimal_value(payment["received"]) if payment.get("received") is not None else None
        )
        reference = str(payment.get("reference") or "").strip()
        if (
            method not in ["CASH", "CARD"]
            or not 0 < amount < Decimal("10000000000")
            or amount != money(amount)
        ):
            raise ValidationError("Pago no válido.")
        if method == "CARD" and not reference:
            raise ValidationError("Confirme la referencia del datáfono externo.")
        if len(reference) > 100:
            raise ValidationError("Referencia demasiado larga.")
        if received is not None and (
            received < amount or received >= Decimal("10000000000") or received != money(received)
        ):
            raise ValidationError("Efectivo recibido insuficiente o no válido.")
        normalized.append(
            {
                "method": method,
                "amount": str(money(amount)),
                "received": str(money(received)) if received is not None else None,
                "reference": reference,
            }
        )
    payload = {
        "ticket": ticket.pk,
        "payments": normalized,
        "cash_session": getattr(cash_session, "pk", None),
    }
    if terminal is not None:
        _validate_terminal(terminal)
        payload["terminal"] = terminal.pk
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    existing = Sale.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise ValidationError("Clave de cobro reutilizada con otros datos.")
        return existing
    ticket = _lock_ticket(ticket, expected_version, ("OPEN", "PAYMENT_PENDING"))
    if terminal is not None:
        OpenTicket.objects.filter(pk=ticket.pk).update(terminal=terminal)
        ticket.terminal = terminal
    lines = list(ticket.lines.all())
    total = sum((line.total for line in lines), Decimal("0"))
    if (
        not 0 < total < Decimal("10000000000")
        or sum((Decimal(p["amount"]) for p in normalized), Decimal("0")) != total
    ):
        raise ValidationError("Los pagos deben sumar exactamente el total positivo.")
    cash_amount = sum(
        (Decimal(p["amount"]) for p in normalized if p["method"] == "CASH"), Decimal("0")
    )
    if cash_amount or cash_session is not None:
        from apps.cash.models import CashSession

        if (
            cash_session is None
            or not CashSession.objects.filter(
                pk=cash_session.pk, closed_at__isnull=True, register__active=True
            ).exists()
        ):
            raise ValidationError("Abra una caja para el efectivo.")
        current_session = CashSession.objects.select_related("register__terminal").get(
            pk=cash_session.pk
        )
        if current_session.register.terminal_id and not current_session.register.terminal.active:
            raise ValidationError("Terminal de caja desactivada.")
        if terminal and current_session.register.terminal_id not in (None, terminal.pk):
            raise ValidationError("La caja está asignada a otra terminal.")
        if current_session.expected_balance + cash_amount >= Decimal("10000000000"):
            raise ValidationError("Saldo fuera del limite de caja.")
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
            cash_session=cash_session,
        )
    from apps.billing.services import issue_invoice
    from apps.hardware.services import enqueue_invoice

    invoice = issue_invoice(sale, actor)
    enqueue_invoice(invoice, actor, open_drawer=cash_amount > 0)
    OpenTicket.objects.filter(
        pk=ticket.pk, status__in=["OPEN", "PAYMENT_PENDING"], version=ticket.version
    ).update(status="CLOSED")
    record(actor, "sale.checkout", obj=sale, metadata={"total": str(total)})
    return sale
