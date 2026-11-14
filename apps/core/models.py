from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class CompanySettings(models.Model):
    name = models.CharField(max_length=200, default="Mi empresa")
    trade_name = models.CharField(max_length=200, blank=True, verbose_name="Nombre comercial")
    commercial_address = models.CharField(
        max_length=500, blank=True, verbose_name="Dirección comercial"
    )
    phone = models.CharField(max_length=40, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Correo electrónico")
    ticket_footer = models.CharField(
        max_length=300, blank=True, verbose_name="Pie de comprobantes futuros"
    )
    logo_data = models.BinaryField(blank=True, default=bytes, editable=False)
    theme = models.CharField(
        max_length=16, choices=[("sage", "Salvia"), ("ocean", "Océano")], default="sage"
    )
    floor_density = models.CharField(
        max_length=16,
        choices=[("comfortable", "Cómoda"), ("compact", "Compacta")],
        default="comfortable",
    )
    state_palette = models.CharField(
        max_length=20,
        choices=[("standard", "Estándar"), ("high_contrast", "Contraste reforzado")],
        default="standard",
    )
    default_section = models.ForeignKey(
        "layout.Section",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="company_preferences",
    )
    tax_id = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default="EUR")
    timezone = models.CharField(max_length=64, default="Europe/Madrid")
    fiscal_mode = models.CharField(
        max_length=10, choices=[("TEST", "Pruebas"), ("PRODUCTION", "Producción")], default="TEST"
    )
    software_name = models.CharField(max_length=100, default="BeautyTPV")
    software_version = models.CharField(max_length=30, default="0.1.0")
    producer_name = models.CharField(max_length=200, blank=True)
    producer_tax_id = models.CharField(max_length=20, blank=True)
    installation_number = models.CharField(max_length=30, default="1")
    quick_sale_enabled = models.BooleanField(default=False)
    simplified_series = models.CharField(
        max_length=12,
        default="S",
        validators=[
            RegexValidator(r"^[A-Z0-9_-]+$", "Use letras mayusculas, numeros, guion o subrayado.")
        ],
    )
    full_series = models.CharField(
        max_length=12,
        default="F",
        validators=[
            RegexValidator(r"^[A-Z0-9_-]+$", "Use letras mayusculas, numeros, guion o subrayado.")
        ],
    )
    rectification_series = models.CharField(
        max_length=12,
        default="R",
        validators=[
            RegexValidator(r"^[A-Z0-9_-]+$", "Use letras mayusculas, numeros, guion o subrayado.")
        ],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(pk=1), name="single_company_installation")
        ]

    def clean(self):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValidationError({"timezone": "Zona horaria no valida."}) from None
        if self.currency != "EUR":
            raise ValidationError({"currency": "Esta instalación solo admite EUR."})
        if len({self.simplified_series, self.full_series, self.rectification_series}) != 3:
            raise ValidationError(
                "Las series simplificada, completa y rectificativa deben ser distintas."
            )

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def __str__(self):
        return self.name


class Terminal(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    bridge_token_hash = models.CharField(max_length=128, blank=True, editable=False)

    default_section = models.ForeignKey(
        "layout.Section",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="terminal_preferences",
    )
    default_register = models.ForeignKey(
        "cash.CashRegister",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="preferred_by_terminals",
    )

    def clean(self):
        super().clean()
        if self.default_register_id:
            from apps.cash.models import CashRegister

            register = CashRegister.objects.filter(pk=self.default_register_id).first()
            if (
                register is None
                or not register.active
                or (register.terminal_id and register.terminal_id != self.pk)
            ):
                raise ValidationError(
                    {
                        "default_register": "Seleccione una caja activa compartida o asignada a esta terminal."
                    }
                )

    def set_bridge_token(self, raw):
        if not isinstance(raw, str) or not 32 <= len(raw) <= 256:
            raise ValidationError("El token del bridge debe tener entre 32 y 256 caracteres.")
        self.bridge_token_hash = make_password(raw)

    def check_bridge_token(self, raw):
        return (
            self.active
            and isinstance(raw, str)
            and 32 <= len(raw) <= 256
            and bool(self.bridge_token_hash)
            and check_password(raw, self.bridge_token_hash)
        )

    def __str__(self):
        return self.name
