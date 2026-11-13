from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    for operation in ("UPDATE", "DELETE"):
        schema_editor.execute(
            f"CREATE TRIGGER cash_movement_{operation.lower()} BEFORE {operation} "
            "ON cash_cashmovement BEGIN SELECT RAISE(ABORT, 'Cash movement immutable'); END"
        )
        schema_editor.execute(
            f"CREATE TRIGGER closed_cash_{operation.lower()} BEFORE {operation} "
            "ON cash_cashsession WHEN OLD.closed_at IS NOT NULL "
            "BEGIN SELECT RAISE(ABORT, 'Closed cash session immutable'); END"
        )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for prefix in ("cash_movement", "closed_cash"):
            for operation in ("update", "delete"):
                schema_editor.execute(f"DROP TRIGGER IF EXISTS {prefix}_{operation}")


class Migration(migrations.Migration):
    dependencies = [("cash", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
