from django.db import models
from django.utils import timezone

from apps.billing.models import ImmutableModel


class FiscalRecord(ImmutableModel):
    invoice = models.ForeignKey(
        "billing.Invoice", on_delete=models.PROTECT, related_name="fiscal_records"
    )
    record_type = models.CharField(max_length=12, default="ALTA")
    previous = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="successor"
    )
    fingerprint = models.CharField(max_length=64)
    canonical_payload = models.TextField()
    generated_at = models.CharField(max_length=40)
    created_at = models.DateTimeField(default=timezone.now)
    xml = models.TextField()


class FiscalOutbox(models.Model):
    record = models.OneToOneField(FiscalRecord, on_delete=models.PROTECT, related_name="outbox")
    status = models.CharField(max_length=24, default="PENDING", db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    lease_until = models.DateTimeField(null=True, blank=True)
    lease_token = models.CharField(max_length=32, blank=True)
    last_error = models.CharField(max_length=500, blank=True)


class FiscalTransmission(ImmutableModel):
    outbox = models.ForeignKey(FiscalOutbox, on_delete=models.PROTECT, related_name="transmissions")
    requested_at = models.DateTimeField(default=timezone.now)
    response = models.TextField(blank=True)
    status = models.CharField(max_length=20)


class FiscalEndpointState(models.Model):
    """One shared flow-control lease per AEAT endpoint in this installation."""

    environment = models.CharField(max_length=10, unique=True)
    next_allowed_at = models.DateTimeField(default=timezone.now)
    lease_until = models.DateTimeField(null=True, blank=True)
    lease_token = models.CharField(max_length=32, blank=True)
