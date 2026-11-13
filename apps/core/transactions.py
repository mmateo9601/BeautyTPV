"""Retry an entire short SQLite unit after rollback, never a partial statement."""

import time
from functools import wraps

from django.core.exceptions import ValidationError
from django.db import OperationalError, connection, transaction


def atomic_retry(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        nested = connection.in_atomic_block
        for attempt in range(4):
            try:
                with transaction.atomic():
                    return function(*args, **kwargs)
            except OperationalError as error:
                locked = "locked" in str(error).lower() or "busy" in str(error).lower()
                if connection.vendor != "sqlite" or not locked or nested:
                    raise
                if attempt == 3:
                    raise ValidationError(
                        "La base esta ocupada. Recargue y reintente con la misma clave de cobro."
                    ) from error
                # atomic has already rolled back the whole failed unit here.
                time.sleep(0.05 * 2**attempt)

    return wrapped
