from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    legal_basis = models.CharField(
        max_length=200, default="Ejecución de contrato y obligaciones fiscales"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
