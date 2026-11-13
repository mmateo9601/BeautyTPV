"""External certificate references only; private key bytes never enter the database."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


def fiscal_configuration():
    from .models import TechnicalSettings

    configuration = TechnicalSettings.load()
    return {
        "certificate": configuration.certificate_path or getattr(settings, "AEAT_CERTIFICATE", ""),
        "private_key": configuration.private_key_path or getattr(settings, "AEAT_PRIVATE_KEY", ""),
        "environment": configuration.fiscal_environment,
    }


def validate_certificate_references(certificate, private_key):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    if not certificate and not private_key:
        return None
    if not certificate or not private_key:
        raise ValidationError("Configure ambas referencias: certificado y clave privada externos.")
    root = Path(settings.BASE_DIR).resolve()
    paths = [Path(certificate), Path(private_key)]
    if any(
        not path.is_absolute() or path.resolve().is_relative_to(root) or not path.is_file()
        for path in paths
    ):
        raise ValidationError(
            "Certificado y clave deben ser archivos absolutos existentes fuera del repositorio."
        )
    try:
        cert = x509.load_pem_x509_certificate(paths[0].read_bytes())
        key = serialization.load_pem_private_key(paths[1].read_bytes(), password=None)
        public = serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        if cert.public_key().public_bytes(*public) != key.public_key().public_bytes(*public):
            raise ValidationError("La clave privada no corresponde al certificado.")
        if not cert.not_valid_before_utc <= timezone.now() <= cert.not_valid_after_utc:
            raise ValidationError("Certificado caducado o todavía no válido.")
        return cert.not_valid_after_utc.isoformat()
    except (OSError, ValueError, TypeError) as error:
        raise ValidationError(
            "Referencia no legible o formato PEM no admitido; configure claves externas con permisos OS restrictivos."
        ) from error
