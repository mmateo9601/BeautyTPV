from contextlib import contextmanager
from contextvars import ContextVar

current_terminal_id = ContextVar("beautytpv_audit_terminal_id", default=None)


@contextmanager
def terminal_context(terminal_id):
    token = current_terminal_id.set(terminal_id)
    try:
        yield
    finally:
        current_terminal_id.reset(token)
