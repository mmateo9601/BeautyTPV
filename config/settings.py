import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("BEAUTYTPV_DEBUG", "1") == "1"
SECRET_KEY = os.getenv("BEAUTYTPV_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Configure BEAUTYTPV_SECRET_KEY fuera del repositorio")
    SECRET_KEY = "development-only-not-for-production-beautytpv"
ALLOWED_HOSTS = os.getenv("BEAUTYTPV_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.TerminalContextMiddleware",
    "config.middleware.CompanyTimezoneMiddleware",
    "apps.support.middleware.MaintenanceMiddleware",
    "apps.accounts.middleware.SupportPIIMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "config.context_processors.installation",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("BEAUTYTPV_DB", str(BASE_DIR / "db.sqlite3")),
        "OPTIONS": {"timeout": 20, "transaction_mode": "IMMEDIATE"},
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/acceso/"
LOGIN_REDIRECT_URL = "/tpv/"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = not DEBUG
FISCAL_ENVIRONMENT = os.getenv("BEAUTYTPV_FISCAL_ENVIRONMENT", "TEST")
FISCAL_PRODUCTION_APPROVED = False
HARDWARE_SIMULATOR = DEBUG

AUTH_USER_MODEL = "accounts.User"
INSTALLED_APPS += ["apps.accounts", "apps.audit"]

INSTALLED_APPS += [
    "apps.core",
    "apps.layout",
    "apps.catalog",
    "apps.customers",
    "apps.pos",
    "apps.cash",
    "apps.reports",
    "apps.billing",
    "apps.verifactu",
]


INSTALLED_APPS += ["apps.hardware"]

INSTALLED_APPS += ["apps.support"]

AEAT_CERTIFICATE = os.getenv("BEAUTYTPV_AEAT_CERTIFICATE", "")
AEAT_PRIVATE_KEY = os.getenv("BEAUTYTPV_AEAT_PRIVATE_KEY", "")
APP_VERSION = "0.1.0"

# Enable only with a trusted loopback proxy that overwrites this header.
if os.getenv("BEAUTYTPV_TRUST_PROXY", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    value for value in os.getenv("BEAUTYTPV_CSRF_TRUSTED_ORIGINS", "").split(",") if value
]
SECURE_HSTS_SECONDS = int(os.getenv("BEAUTYTPV_HSTS_SECONDS", "0" if DEBUG else "31536000"))
