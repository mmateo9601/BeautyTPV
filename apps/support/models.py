from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.pos.models import ImmutableQuerySet


class SupportSession(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_sessions"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_approvals"
    )
    justification = models.CharField(max_length=500)
    scope = models.CharField(max_length=30, default="TECHNICAL")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    @property
    def active(self):
        return self.revoked_at is None and self.expires_at > timezone.now()


class BackupRun(models.Model):
    filename = models.CharField(max_length=120)
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default="COMPLETE")

    def __str__(self):
        return self.filename


class UpdateRun(models.Model):
    version = models.CharField(max_length=40)
    package_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=200, blank=True)


class TechnicalSettings(models.Model):
    backup_retention_days = models.PositiveIntegerField(
        default=30, validators=[MinValueValidator(1)]
    )
    backup_interval_hours = models.PositiveIntegerField(
        default=24, validators=[MinValueValidator(1)]
    )
    certificate_path = models.CharField(max_length=500, blank=True)
    private_key_path = models.CharField(max_length=500, blank=True)
    fiscal_environment = models.CharField(
        max_length=10,
        choices=[("TEST", "Pruebas"), ("PRODUCTION", "Producción bloqueada hasta validación")],
        default="TEST",
    )
    updates_channel = models.CharField(max_length=20, default="manual-verified")
    maintenance = models.BooleanField(default=False)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]


class ServiceHeartbeat(models.Model):
    name = models.CharField(max_length=40, unique=True)
    pid = models.PositiveIntegerField()
    state = models.CharField(max_length=20, default="RUNNING")
    last_seen = models.DateTimeField(default=timezone.now)
    last_error_code = models.CharField(max_length=100, blank=True)


class Incident(models.Model):
    class Category(models.TextChoices):
        OPERATIONAL = "OPERATIONAL", "Operativa"
        HARDWARE = "HARDWARE", "Dispositivos"
        FISCAL = "FISCAL", "Cola fiscal"
        SYSTEM = "SYSTEM", "Sistema"

    class Severity(models.TextChoices):
        LOW = "LOW", "Baja"
        MEDIUM = "MEDIUM", "Media"
        HIGH = "HIGH", "Alta"
        CRITICAL = "CRITICAL", "Critica"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Abierta"
        IN_PROGRESS = "IN_PROGRESS", "En curso"
        RESOLVED = "RESOLVED", "Resuelta"

    title = models.CharField(max_length=160)
    description = models.CharField(max_length=1000)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OPERATIONAL
    )
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-updated_at", "-pk"]

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        raise ValidationError("Las incidencias se conservan con su historial.")

    def __str__(self):
        return self.title


class IncidentAction(models.Model):
    objects = ImmutableQuerySet.as_manager()

    incident = models.ForeignKey(Incident, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=1000)
    previous_status = models.CharField(max_length=20, choices=Incident.Status.choices)
    new_status = models.CharField(max_length=20, choices=Incident.Status.choices)
    previous_category = models.CharField(max_length=20, choices=Incident.Category.choices)
    new_category = models.CharField(max_length=20, choices=Incident.Category.choices)
    previous_severity = models.CharField(max_length=10, choices=Incident.Severity.choices)
    new_severity = models.CharField(max_length=10, choices=Incident.Severity.choices)

    class Meta:
        ordering = ["created_at", "pk"]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.pk:
            raise ValidationError("Una actuacion registrada no se puede modificar.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        raise ValidationError("Una actuacion registrada no se puede eliminar.")
