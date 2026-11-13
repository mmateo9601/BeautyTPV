from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(
            "CREATE TRIGGER immutable_audit_event_replace BEFORE INSERT ON audit_auditevent "
            "WHEN EXISTS (SELECT 1 FROM audit_auditevent WHERE id=NEW.id) "
            "BEGIN SELECT RAISE(ABORT, 'Audit evidence cannot be replaced'); END"
        )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute("DROP TRIGGER IF EXISTS immutable_audit_event_replace")


class Migration(migrations.Migration):
    dependencies = [("audit", "0002_append_only_triggers")]
    operations = [migrations.RunPython(protect, unprotect)]
