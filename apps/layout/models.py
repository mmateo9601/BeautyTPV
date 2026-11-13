from django.core.exceptions import ValidationError
from django.db import models


class Section(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Station(models.Model):
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="stations")
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.tickets.filter(status__in=["OPEN", "PAYMENT_PENDING"]).exists():
            raise ValidationError("Puesto con cuenta abierta.")
        return super().delete(*args, **kwargs)
