from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    sort_order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    visible_in_pos = models.BooleanField(default=True, verbose_name="Visible en TPV")

    class Meta:
        ordering = ["sort_order", "name", "pk"]

    def __str__(self):
        return self.name


class CatalogItem(models.Model):
    class Kind(models.TextChoices):
        SERVICE = "SERVICE", "Servicio"
        PRODUCT = "PRODUCT", "Producto"

    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SERVICE)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=21,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ["sort_order", "name", "pk"]
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="catalog_nonnegative_price"),
            models.CheckConstraint(
                condition=Q(tax_rate__gte=0, tax_rate__lte=100), name="catalog_valid_tax"
            ),
        ]

    def __str__(self):
        return self.name
