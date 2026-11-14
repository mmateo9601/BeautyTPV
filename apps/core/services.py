"""Validated installation settings; historical fiscal snapshots are never modified."""

import io
import warnings

from django.core.exceptions import ValidationError
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from apps.accounts.permissions import require_role
from apps.audit.services import record

from .models import CompanySettings

COMPANY_FIELDS = frozenset(
    {
        "name",
        "tax_id",
        "address",
        "timezone",
        "producer_name",
        "producer_tax_id",
        "installation_number",
        "quick_sale_enabled",
        "simplified_series",
        "full_series",
        "rectification_series",
        "trade_name",
        "commercial_address",
        "phone",
        "email",
        "ticket_footer",
        "theme",
        "floor_density",
        "state_palette",
        "default_section",
        "currency",
    }
)


def canonical_logo(upload):
    if getattr(upload, "size", 0) > 2 * 1024 * 1024:
        raise ValidationError("El logotipo no puede superar 2 MiB.")
    raw = upload.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValidationError("El logotipo no puede superar 2 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if (
                    image.format not in ("PNG", "JPEG", "WEBP")
                    or image.width * image.height > 16_000_000
                ):
                    raise ValueError
                image.load()
                image = image.convert("RGBA")
                image.thumbnail((600, 600))
                target = io.BytesIO()
                image.save(target, format="PNG", optimize=True)
                result = target.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValidationError(
            "Suba una imagen PNG, JPEG o WebP válida de hasta 16 megapíxeles."
        ) from None
    if len(result) > 256 * 1024:
        raise ValidationError(
            "El logotipo normalizado supera 256 KiB; use una imagen más sencilla."
        )
    return result


@transaction.atomic
def save_company_settings(actor, data, logo=None, remove_logo=False):
    require_role(actor, "ADMIN")
    if set(data) - COMPANY_FIELDS:
        raise ValidationError("Parámetro de configuración no permitido.")
    company = CompanySettings.load()
    previous_identity = (company.tax_id, company.installation_number)
    for name, value in data.items():
        setattr(company, name, value)
    from apps.billing.models import Invoice

    if Invoice.objects.exists() and previous_identity != (
        company.tax_id,
        company.installation_number,
    ):
        raise ValidationError(
            "Tras emitir facturas no puede cambiar el NIF ni la identificación de instalación; requiere una instalación independiente."
        )
    if remove_logo and logo:
        raise ValidationError("Seleccione subir o retirar el logotipo, no ambas acciones.")
    if logo:
        company.logo_data = canonical_logo(logo)
    elif remove_logo:
        company.logo_data = b""
    company.full_clean()
    company.save()
    record(actor, "company.settings", obj=company)
    return company
