from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Registro emitido inmutable.")

    def delete(self):
        raise ValidationError("Registro emitido inmutable.")


class ImmutableModel(models.Model):
    objects = ImmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Registro emitido inmutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Registro emitido inmutable.")


class OpenTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Abierta"
        PAYMENT_PENDING = "PAYMENT_PENDING", "En cobro"
        CLOSED = "CLOSED", "Cerrada"
        CANCELLED = "CANCELLED", "Anulada"

    station = models.ForeignKey(
        "layout.Station", on_delete=models.PROTECT, null=True, blank=True, related_name="tickets"
    )
    terminal = models.ForeignKey("core.Terminal", null=True, blank=True, on_delete=models.PROTECT)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tickets",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cancelled_tickets",
    )
    version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["station"],
                condition=Q(status__in=["OPEN", "PAYMENT_PENDING"]),
                name="one_active_ticket_per_station",
            )
        ]

    @property
    def total(self):
        return sum((line.total for line in self.lines.all()), Decimal("0.00"))

    def delete(self, *args, **kwargs):
        raise ValidationError("Las cuentas se anulan, no se borran.")


class TicketLine(models.Model):
    ticket = models.ForeignKey(OpenTicket, on_delete=models.PROTECT, related_name="lines")
    item = models.ForeignKey("catalog.CatalogItem", on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=250)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    quantity__gt=0,
                    unit_price__gte=0,
                    tax_rate__gte=0,
                    tax_rate__lte=100,
                    discount_percent__gte=0,
                    discount_percent__lte=100,
                ),
                name="valid_ticket_line",
            )
        ]

    @property
    def total(self):
        return money(self.quantity * self.unit_price * (1 - self.discount_percent / 100))

    @property
    def net_total(self):
        return money(self.total / (1 + self.tax_rate / 100))

    @property
    def tax_total(self):
        return self.total - self.net_total

    def save(self, *args, **kwargs):
        if self.ticket.status != "OPEN":
            raise ValidationError("Cuenta no editable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.ticket.status != "OPEN":
            raise ValidationError("Cuenta no editable.")
        return super().delete(*args, **kwargs)


class Sale(ImmutableModel):
    ticket = models.OneToOneField(OpenTicket, on_delete=models.PROTECT, related_name="sale")
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=100, unique=True)
    request_fingerprint = models.CharField(max_length=64)

    @property
    def customer(self):
        return self.ticket.customer


class Payment(ImmutableModel):
    class Method(models.TextChoices):
        CASH = "CASH", "Efectivo"
        CARD = "CARD", "Tarjeta"

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    received = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    cash_session = models.ForeignKey(
        "cash.CashSession", on_delete=models.PROTECT, null=True, blank=True, related_name="payments"
    )

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="positive_payment")]

    @property
    def change(self):
        return (self.received - self.amount) if self.received is not None else Decimal("0.00")
