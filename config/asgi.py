import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()

from config.lifecycle import hold_service_lock  # noqa: E402

_service_lock = hold_service_lock()
