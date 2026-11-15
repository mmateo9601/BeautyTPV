"""Explicit offline, loopback-only DEMO. Production settings remain unchanged."""

import os

from scripts.demo_config import demo_directory, read_configuration

DEMO_DIRECTORY = demo_directory(os.environ.get("BEAUTYTPV_DEMO_DIR"))
_configuration = read_configuration(DEMO_DIRECTORY)
# Set before importing base: never inherit a production database or secret.
os.environ["BEAUTYTPV_DEBUG"] = "0"
os.environ["BEAUTYTPV_SECRET_KEY"] = _configuration["secret_key"]

from .settings import *  # noqa: E402,F403

LOCAL_DEMO_ONLY = True
DEBUG = False
SECRET_KEY = _configuration["secret_key"]
DATABASES["default"]["NAME"] = str(DEMO_DIRECTORY / "demo.sqlite3")  # noqa: F405
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
STATIC_ROOT = DEMO_DIRECTORY / "staticfiles"
SESSION_COOKIE_NAME = "beautytpv_demo_session"
CSRF_COOKIE_NAME = "beautytpv_demo_csrf"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = None
CSRF_TRUSTED_ORIGINS = []
FISCAL_ENVIRONMENT = "TEST"
FISCAL_PRODUCTION_APPROVED = False
FISCAL_APPROVAL_EVIDENCE = ""
FISCAL_RESTORE_HOLD = True  # send_one stops before DB/transport; sales stay usable.
AEAT_CERTIFICATE = ""
AEAT_PRIVATE_KEY = ""
HARDWARE_SIMULATOR = True
os.environ["BEAUTYTPV_BACKUP_KEY"] = _configuration["backup_key"]
os.environ["BEAUTYTPV_BACKUP_DIR"] = str(DEMO_DIRECTORY / "backups")
os.environ["BEAUTYTPV_FISCAL_ENVIRONMENT"] = "TEST"
os.environ["BEAUTYTPV_AEAT_CERTIFICATE"] = ""
os.environ["BEAUTYTPV_AEAT_PRIVATE_KEY"] = ""


class LocalDemoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.http import HttpResponse

        if request.META.get("REMOTE_ADDR") not in ("127.0.0.1", "::1"):
            return HttpResponse("La DEMO solo admite localhost.", status=403)
        if request.method == "POST":
            if request.path == "/soporte/fiscal/":
                return HttpResponse(
                    "DEMO: entorno TEST fijo, sin certificados ni remision AEAT.", status=403
                )
            if request.path == "/soporte/diagnostico/" and request.POST.get("network"):
                return HttpResponse(
                    "DEMO sin conexiones externas. Desmarque la prueba de red AEAT.", status=403
                )
            if (
                request.path.startswith("/soporte/dispositivos/")
                and request.POST.get("connection_type") != "SIMULATOR"
            ):
                return HttpResponse("DEMO: solo se admite la impresora simulada.", status=400)
        return self.get_response(request)


MIDDLEWARE = ["config.demo_settings.LocalDemoMiddleware", *MIDDLEWARE]  # noqa: F405
