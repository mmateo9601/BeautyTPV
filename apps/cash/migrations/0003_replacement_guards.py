from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table, condition in (
            ("cash_cashmovement", "id=NEW.id"),
            ("cash_cashsession", "id=NEW.id AND closed_at IS NOT NULL"),
        ):
            schema_editor.execute(
                f"CREATE TRIGGER no_replace_{table} BEFORE INSERT ON {table} "
                f"WHEN EXISTS (SELECT 1 FROM {table} WHERE {condition}) "
                "BEGIN SELECT RAISE(ABORT, 'Cash history replacement prohibited'); END"
            )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table in ("cash_cashmovement", "cash_cashsession"):
            schema_editor.execute(f"DROP TRIGGER IF EXISTS no_replace_{table}")


class Migration(migrations.Migration):
    dependencies = [("cash", "0002_cash_guards")]
    operations = [migrations.RunPython(protect, unprotect)]
