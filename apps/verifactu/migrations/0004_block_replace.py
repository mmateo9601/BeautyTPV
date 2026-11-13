from django.db import migrations

GUARDS = {
    "verifactu_fiscalrecord": "EXISTS (SELECT 1 FROM verifactu_fiscalrecord WHERE id=NEW.id OR (NEW.previous_id IS NOT NULL AND previous_id=NEW.previous_id))",
    "verifactu_fiscaltransmission": "EXISTS (SELECT 1 FROM verifactu_fiscaltransmission WHERE id=NEW.id)",
}


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table, condition in GUARDS.items():
            schema_editor.execute(
                f"CREATE TRIGGER no_replace_{table} BEFORE INSERT ON {table} WHEN {condition} BEGIN SELECT RAISE(ABORT, 'Issued record cannot be replaced'); END"
            )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table in GUARDS:
            schema_editor.execute(f"DROP TRIGGER IF EXISTS no_replace_{table}")


class Migration(migrations.Migration):
    dependencies = [("verifactu", "0003_endpoint_flow_control")]
    operations = [migrations.RunPython(protect, unprotect)]
