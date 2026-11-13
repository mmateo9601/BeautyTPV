import atexit

from django.conf import settings

from apps.support.operations import service_lock


def hold_service_lock():
    guard = service_lock(settings.DATABASES["default"]["NAME"])
    guard.__enter__()
    atexit.register(guard.__exit__, None, None, None)
    return guard
