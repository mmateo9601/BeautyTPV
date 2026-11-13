from django.db import migrations


def backfill(apps, schema_editor):
    """Recover historical cancellation time from immutable evidence, never guess a date."""
    if schema_editor.connection.vendor != "sqlite":
        return
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='pos_openticket'"
        )
        guards = [
            (name, sql) for name, sql in cursor.fetchall() if sql and "BEFORE UPDATE" in sql.upper()
        ]
    for name, _ in guards:
        schema_editor.execute(f"DROP TRIGGER {schema_editor.quote_name(name)}")
    try:
        Event = apps.get_model("audit", "AuditEvent")
        Ticket = apps.get_model("pos", "OpenTicket")
        seen = set()
        for target, actor, created_at in (
            Event.objects.using(connection.alias)
            .filter(action="ticket.cancel")
            .order_by("created_at", "pk")
            .values_list("target", "actor_id", "created_at")
        ):
            prefix = "pos.OpenTicket:"
            identifier = target[len(prefix) :] if target.startswith(prefix) else ""
            if not identifier.isascii() or not identifier.isdigit() or identifier in seen:
                continue
            seen.add(identifier)
            Ticket.objects.using(connection.alias).filter(
                pk=int(identifier), status="CANCELLED", cancelled_at__isnull=True
            ).update(cancelled_at=created_at, cancelled_by_id=actor)
    finally:
        for _, statement in guards:
            schema_editor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [("pos", "0006_ticket_cancellation_audit"), ("audit", "0001_initial")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
