from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for operation in ("UPDATE", "DELETE"):
            schema_editor.execute(
                f"CREATE TRIGGER immutable_audit_event_{operation.lower()} "
                f"BEFORE {operation} ON audit_auditevent "
                "BEGIN SELECT RAISE(ABORT, 'Audit evidence is append-only'); END"
            )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for operation in ("update", "delete"):
            schema_editor.execute(f"DROP TRIGGER IF EXISTS immutable_audit_event_{operation}")


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
