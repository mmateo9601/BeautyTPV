from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.audit.services import record
from apps.pos.services import decimal_value

from .models import CashMovement, CashSession


def _amount(value):
    value = decimal_value(value)
    if value < 0 or value.as_tuple().exponent < -2:
        raise ValidationError("Importe no válido.")
    return value


@transaction.atomic
def open_session(register, actor, opening_balance):
    require_role(actor, "EMPLOYEE")
    if CashSession.objects.filter(register=register, closed_at__isnull=True).exists():
        raise ValidationError("La caja ya tiene una sesión abierta.")
    session = CashSession.objects.create(
        register=register, opened_by=actor, opening_balance=_amount(opening_balance)
    )
    record(actor, "cash.open", obj=session)
    return session


@transaction.atomic
def add_movement(session, actor, kind, amount, reason):
    require_role(actor, "MANAGER")
    session = CashSession.objects.get(pk=session.pk)
    amount = _amount(amount)
    if session.closed_at or kind not in ["IN", "OUT"] or amount <= 0 or not str(reason).strip():
        raise ValidationError("Movimiento no válido o caja cerrada.")
    if kind == "OUT" and amount > session.expected_balance:
        raise ValidationError("Saldo insuficiente.")
    movement = CashMovement.objects.create(
        session=session, actor=actor, kind=kind, amount=amount, reason=reason
    )
    record(actor, "cash.movement", obj=movement)
    return movement


@transaction.atomic
def close_session(session, actor, counted):
    require_role(actor, "MANAGER")
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
