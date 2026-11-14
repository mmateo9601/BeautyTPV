import codecs

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
    cut_paper = models.BooleanField(default=True, verbose_name="Cortar papel al finalizar")
    drawer_enabled = models.BooleanField(default=True, verbose_name="Cajon conectado y habilitado")
    enabled = models.BooleanField(default=True)
    terminal = models.ForeignKey("core.Terminal", null=True, blank=True, on_delete=models.PROTECT)

    def clean(self):
        errors = {}
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).first()
            destination_fields = (
                "connection_type",
                "address",
                "port",
                "usb_vendor",
                "usb_product",
                "usb_endpoint",
                "terminal_id",
            )
            if original and any(
                getattr(original, field) != getattr(self, field) for field in destination_fields
            ):
                if self.printjob_set.filter(status="SENDING").exists():
                    raise ValidationError(
                        "Hay una entrega en curso. Espere su acuse o concilie su estado antes de cambiar el destino."
                    )
        try:
            codec = codecs.lookup(self.encoding)
            if codec.name not in {
                "ascii",
                "cp437",
                "cp850",
                "cp858",
                "cp1252",
                "iso8859-1",
                "utf-8",
            }:
                errors["encoding"] = (
                    "Use una codificacion ESC/POS admitida: cp437, cp850, cp858, cp1252, latin1 o utf-8."
                )
        except LookupError:
            errors["encoding"] = "Codificacion no reconocida por el servidor."
        if not 0 <= self.codepage <= 255:
            errors["codepage"] = "La pagina ESC/POS debe estar entre 0 y 255."
        if self.connection_type == self.Connection.TCP:
            if not self.address.strip():
                errors["address"] = "Indique el nombre o direccion IP de la impresora."
            if not 1 <= self.port <= 65535:
                errors["port"] = "Puerto TCP no valido."
        elif self.connection_type == self.Connection.USB:
            if not 1 <= self.usb_vendor <= 65535 or not 1 <= self.usb_product <= 65535:
                errors["usb_vendor"] = (
                    "Indique identificadores USB de fabricante y producto validos."
                )
            if not 1 <= self.usb_endpoint <= 255:
                errors["usb_endpoint"] = "Endpoint USB no valido."
        elif self.connection_type == self.Connection.SERIAL:
            if not self.address.strip():
                errors["address"] = "Indique el puerto serie local."
            if not self.port:
                errors["port"] = "La velocidad serie debe ser positiva."
        if errors:
            raise ValidationError(errors)

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
    encoding = models.CharField(max_length=20, default="cp858")
    codepage = models.PositiveSmallIntegerField(default=19)
    open_drawer = models.BooleanField(default=False)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    lease_token = models.CharField(max_length=64, blank=True, editable=False)
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
            for field in [
                "invoice_id",
                "kind",
                "payload",
                "open_drawer",
                "requested_by_id",
                "encoding",
                "codepage",
            ]:
                if getattr(original, field) != getattr(self, field):
                    raise ValidationError("La intención de impresión es inmutable.")
        return super().save(*args, **kwargs)


class HardwareEvent(models.Model):
    job = models.ForeignKey(PrintJob, null=True, blank=True, on_delete=models.PROTECT)
    printer = models.ForeignKey(Printer, null=True, blank=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)
    message = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
