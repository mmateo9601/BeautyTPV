import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

from config.lifecycle import hold_service_lock  # noqa: E402

_service_lock = hold_service_lock()
