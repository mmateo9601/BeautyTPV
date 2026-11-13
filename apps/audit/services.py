from .models import AuditEvent

ALLOWED_METADATA = {
    "reason",
    "scope",
    "role",
    "previous_role",
    "count",
    "status",
    "method",
    "amount",
    "version",
    "error_code",
    "session_id",
    "terminal_id",
    "invoice_id",
    "sale_id",
    "job_id",
    "file_id",
    "sha256",
}


def record(actor=None, action="", target="", metadata=None, obj=None, outcome="SUCCESS"):
    if obj is not None:
        target = f"{obj._meta.label}:{obj.pk}"
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    clean = {}
    for key, value in (metadata or {}).items():
        if key == "sha256" and (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in value)
        ):
            continue
        if key in ALLOWED_METADATA and isinstance(value, (str, int, float, bool, type(None))):
            clean[key] = value[:500] if isinstance(value, str) else value
    return AuditEvent.objects.create(
        actor=actor,
        action=action[:100],
        target=str(target)[:160],
        metadata=clean,
        outcome=outcome[:30],
    )
