from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("La auditoría es inmutable.")

    def delete(self):
        raise ValidationError("La auditoría es inmutable.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("La auditoría es inmutable.")


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT
    )
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=160, blank=True)
    outcome = models.CharField(max_length=30, default="SUCCESS")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("La auditoría es inmutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("La auditoría es inmutable.")
