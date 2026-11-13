from django.db import models


class CompanySettings(models.Model):
    name = models.CharField(max_length=200, default="Mi empresa")
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

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def __str__(self):
        return self.name
