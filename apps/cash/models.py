from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum

from apps.pos.models import ImmutableModel


class CashRegister(models.Model):
    name = models.CharField(max_length=100, unique=True)

    active = models.BooleanField(default=True)
    terminal = models.ForeignKey(
        "core.Terminal",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cash_registers",
    )

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class CashSession(models.Model):
    register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name="sessions")
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_cash_sessions"
    )
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="closed_cash_sessions",
    )
    counted = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["register"],
                condition=Q(closed_at__isnull=True),
                name="one_open_cash_session",
            ),
            models.CheckConstraint(
                condition=Q(opening_balance__gte=0), name="positive_opening_balance"
            ),
        ]

    @property
    def expected_balance(self):
        paid = self.payments.filter(method="CASH").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        incoming = self.movements.filter(kind="IN").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        outgoing = self.movements.filter(kind="OUT").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        refunds = self.refunds.filter(method="CASH").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        return self.opening_balance + paid + incoming - outgoing - refunds

    def __str__(self):
        return f"{self.register} · {self.pk}"


class CashMovement(ImmutableModel):
    session = models.ForeignKey(CashSession, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=3, choices=[("IN", "Ingreso"), ("OUT", "Retirada")])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=250)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="positive_cash_movement")
        ]
