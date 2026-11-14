from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.audit.services import record
from apps.core.guards import require_operational
from apps.core.transactions import atomic_retry
from apps.pos.services import decimal_value

from .models import CashMovement, CashRegister, CashSession


def _amount(value):
    value = decimal_value(value)
    if value < 0 or value >= Decimal("10000000000") or value.as_tuple().exponent < -2:
        raise ValidationError("Importe no válido.")
    return value


@atomic_retry
def open_session(register, actor, opening_balance):
    require_role(actor, "EMPLOYEE")
    require_operational()
    register = CashRegister.objects.select_related("terminal").get(pk=register.pk)
    if not register.active or (register.terminal_id and not register.terminal.active):
        raise ValidationError("Caja o terminal no disponible.")
    if CashSession.objects.filter(register=register, closed_at__isnull=True).exists():
        raise ValidationError("La caja ya tiene una sesión abierta.")
    session = CashSession.objects.create(
        register=register, opened_by=actor, opening_balance=_amount(opening_balance)
    )
    record(actor, "cash.open", obj=session)
    return session


@atomic_retry
def add_movement(session, actor, kind, amount, reason):
    require_role(actor, "MANAGER")
    require_operational()
    session = CashSession.objects.get(pk=session.pk)
    amount = _amount(amount)
    reason = str(reason).strip()
    if (
        session.closed_at
        or kind not in ["IN", "OUT"]
        or amount <= 0
        or not reason
        or len(reason) > 250
    ):
        raise ValidationError("Movimiento no válido o caja cerrada.")
    if kind == "OUT" and amount > session.expected_balance:
        raise ValidationError("Saldo insuficiente.")
    if kind == "IN" and session.expected_balance + amount >= Decimal("10000000000"):
        raise ValidationError("Saldo fuera del limite de caja.")
    movement = CashMovement.objects.create(
        session=session, actor=actor, kind=kind, amount=amount, reason=reason
    )
    record(actor, "cash.movement", obj=movement)
    return movement


@atomic_retry
def close_session(session, actor, counted):
    require_role(actor, "MANAGER")
    require_operational()
    session = CashSession.objects.get(pk=session.pk)
    if session.closed_at:
        raise ValidationError("La caja ya está cerrada.")
    session.counted = _amount(counted)
    session.expected = session.expected_balance
    session.difference = session.counted - session.expected
    session.closed_at = timezone.now()
    session.closed_by = actor
    session.save(update_fields=["counted", "expected", "difference", "closed_at", "closed_by"])
    record(actor, "cash.close", obj=session, metadata={"difference": str(session.difference)})
    return session


@atomic_retry
def save_register(actor, register):
    require_role(actor, "ADMIN")
    if register.pk:
        current = CashRegister.objects.get(pk=register.pk)
        if current.sessions.filter(closed_at__isnull=True).exists() and (
            not register.active or register.terminal_id != current.terminal_id
        ):
            raise ValidationError("No puede desactivar ni reasignar una caja con turno abierto.")
    if register.terminal_id:
        from apps.core.models import Terminal

        terminal = Terminal.objects.filter(pk=register.terminal_id, active=True).first()
        if terminal is None:
            raise ValidationError("La terminal seleccionada está desactivada.")
        register.terminal = terminal
    register.full_clean()
    register.save()
    record(actor, "cash.register.saved", obj=register)
    return register
