from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Documento emitido inmutable.")

    def delete(self):
        raise ValidationError("Documento emitido inmutable.")


class ImmutableModel(models.Model):
    objects = ImmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Documento emitido inmutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Documento emitido inmutable.")


class InvoiceSequence(models.Model):
    series = models.CharField(max_length=12)
    year = models.PositiveIntegerField()
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["series", "year"], name="invoice_sequence_unique")
        ]


class Invoice(ImmutableModel):
    sale = models.OneToOneField(
        "pos.Sale", null=True, blank=True, on_delete=models.PROTECT, related_name="invoice"
    )
    series = models.CharField(max_length=12)
    year = models.PositiveIntegerField()
    number = models.PositiveIntegerField()
    invoice_type = models.CharField(max_length=2, default="F2")
    issued_at = models.DateTimeField()
    issuer = models.JSONField()
    customer = models.JSONField(default=dict)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    net_total = models.DecimalField(max_digits=14, decimal_places=2)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2)
    rectifies = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="rectifications"
    )
    reason = models.CharField(max_length=500, blank=True)
    fiscal_mode = models.CharField(max_length=10, default="TEST")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["series", "year", "number"], name="invoice_number_unique"
            )
        ]
        ordering = ["-id"]

    @property
    def full_number(self):
        return f"{self.series}-{self.year}-{self.number:06d}"

    @property
    def public_number(self):
        return self.full_number

    def __str__(self):
        return self.full_number


class InvoiceLine(ImmutableModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="lines")
    description = models.CharField(max_length=250)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    net_total = models.DecimalField(max_digits=14, decimal_places=2)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)


class Refund(ImmutableModel):
    invoice = models.OneToOneField(Invoice, on_delete=models.PROTECT, related_name="refund")
    method = models.CharField(max_length=4, choices=[("CASH", "Efectivo"), ("CARD", "Tarjeta")])
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    cash_session = models.ForeignKey(
        "cash.CashSession", null=True, blank=True, on_delete=models.PROTECT, related_name="refunds"
    )
    reference = models.CharField(max_length=100, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
