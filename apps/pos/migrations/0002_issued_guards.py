from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    for table in ["pos_sale", "pos_payment"]:
        for op in ["UPDATE", "DELETE"]:
            schema_editor.execute(
                f"CREATE TRIGGER immutable_{table}_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT, 'Issued sale immutable'); END"
            )
    for op in ["UPDATE", "DELETE"]:
        schema_editor.execute(
            f"CREATE TRIGGER closed_ticketline_{op.lower()} BEFORE {op} ON pos_ticketline WHEN (SELECT status FROM pos_openticket WHERE id=OLD.ticket_id) != 'OPEN' BEGIN SELECT RAISE(ABORT, 'Closed ticket line immutable'); END"
        )
    schema_editor.execute(
        "CREATE TRIGGER closed_ticketline_insert BEFORE INSERT ON pos_ticketline WHEN (SELECT status FROM pos_openticket WHERE id=NEW.ticket_id) != 'OPEN' BEGIN SELECT RAISE(ABORT, 'Closed ticket line immutable'); END"
    )
    schema_editor.execute(
        "CREATE TRIGGER closed_ticket_update BEFORE UPDATE ON pos_openticket WHEN OLD.status IN ('CLOSED','CANCELLED') BEGIN SELECT RAISE(ABORT, 'Closed ticket immutable'); END"
    )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    for table in ["pos_sale", "pos_payment"]:
        for op in ["update", "delete"]:
            schema_editor.execute(f"DROP TRIGGER IF EXISTS immutable_{table}_{op}")
    for op in ["update", "delete", "insert"]:
        schema_editor.execute(f"DROP TRIGGER IF EXISTS closed_ticketline_{op}")
    schema_editor.execute("DROP TRIGGER IF EXISTS closed_ticket_update")


class Migration(migrations.Migration):
    dependencies = [("pos", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
