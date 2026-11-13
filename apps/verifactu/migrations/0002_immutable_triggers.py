from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    for table in ["verifactu_fiscalrecord", "verifactu_fiscaltransmission"]:
        for operation in ["UPDATE", "DELETE"]:
            schema_editor.execute(
                f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'Fiscal record is immutable'); END"
            )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table in ["verifactu_fiscalrecord", "verifactu_fiscaltransmission"]:
            for operation in ["update", "delete"]:
                schema_editor.execute(f"DROP TRIGGER IF EXISTS immutable_{table}_{operation}")


class Migration(migrations.Migration):
    dependencies = [("verifactu", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
