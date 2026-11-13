from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Printer(models.Model):
    class Connection(models.TextChoices):
        TCP = "TCP", "Ethernet TCP"
        USB = "USB", "USB"
        SERIAL = "SERIAL", "Serie"
        SIMULATOR = "SIMULATOR", "Simulador (desarrollo)"

    name = models.CharField(max_length=100, unique=True)
    connection_type = models.CharField(max_length=12, choices=Connection.choices)
    address = models.CharField(max_length=250, blank=True)
    port = models.PositiveIntegerField(default=9100)
    usb_vendor = models.PositiveIntegerField(default=0)
    usb_product = models.PositiveIntegerField(default=0)
    usb_endpoint = models.PositiveIntegerField(default=1)
    encoding = models.CharField(max_length=20, default="cp858")
    codepage = models.PositiveSmallIntegerField(default=19)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PrintJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        SENDING = "SENDING", "Enviando"
        DONE = "DONE", "Enviado al dispositivo"
        FAILED = "FAILED", "Fallo antes del envío"
        UNKNOWN = "UNKNOWN", "Entrega incierta: revisar"

    invoice = models.ForeignKey(
        "billing.Invoice",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="print_jobs",
    )
    printer = models.ForeignKey(Printer, null=True, blank=True, on_delete=models.PROTECT)
    kind = models.CharField(
        max_length=10, choices=[(x, x) for x in ["RECEIPT", "COPY", "DRAWER", "TEST"]]
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    payload = models.BinaryField()
    open_drawer = models.BooleanField(default=False)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice"],
                condition=Q(kind="RECEIPT"),
                name="one_original_print_per_invoice",
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            for field in ["invoice_id", "kind", "payload", "open_drawer", "requested_by_id"]:
                if getattr(original, field) != getattr(self, field):
                    raise ValidationError("La intención de impresión es inmutable.")
        return super().save(*args, **kwargs)


class HardwareEvent(models.Model):
    job = models.ForeignKey(PrintJob, null=True, blank=True, on_delete=models.PROTECT)
    printer = models.ForeignKey(Printer, null=True, blank=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)
    message = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
