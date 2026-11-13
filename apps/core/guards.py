from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def require_operational():
    database = settings.DATABASES["default"]["NAME"]
    if Path(str(database) + ".fiscal-restore-hold").exists():
        raise ValidationError(
            "Instalación retenida: concilie facturas, acuses y cola de impresión tras restaurar."
        )
    from apps.support.models import TechnicalSettings

    if TechnicalSettings.objects.filter(pk=1, maintenance=True).exists():
        raise ValidationError("Instalacion en mantenimiento: operativa suspendida por Superadmin.")
