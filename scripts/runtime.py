"""Load a JSON instance file, never execute configuration as code."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ALLOWED = {
    "BEAUTYTPV_SECRET_KEY",
    "BEAUTYTPV_DEBUG",
    "BEAUTYTPV_ALLOWED_HOSTS",
    "BEAUTYTPV_DB",
    "BEAUTYTPV_BACKUP_KEY",
    "BEAUTYTPV_BACKUP_DIR",
    "BEAUTYTPV_FISCAL_ENVIRONMENT",
    "BEAUTYTPV_AEAT_CERTIFICATE",
    "BEAUTYTPV_AEAT_PRIVATE_KEY",
    "BEAUTYTPV_BRIDGE_TOKEN",
    "BEAUTYTPV_TRUST_PROXY",
    "BEAUTYTPV_CSRF_TRUSTED_ORIGINS",
    "BEAUTYTPV_HSTS_SECONDS",
}


def load_instance(filename):
    values = json.loads(Path(filename).read_text(encoding="utf-8"))
    if set(values) - ALLOWED:
        raise ValueError("Claves de configuración no permitidas.")
    for key, value in values.items():
        os.environ[key] = str(value)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    return values
