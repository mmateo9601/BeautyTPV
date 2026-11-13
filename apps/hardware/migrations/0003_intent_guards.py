from django.db import migrations


def snapshot_and_protect(apps, schema_editor):
    Job = apps.get_model("hardware", "PrintJob")
    for job in Job.objects.select_related("printer").all():
        if job.printer:
            Job.objects.filter(pk=job.pk).update(
                encoding=job.printer.encoding, codepage=job.printer.codepage
            )
    if schema_editor.connection.vendor != "sqlite":
        return
    fields = [
        "invoice_id",
        "kind",
        "payload",
        "open_drawer",
        "requested_by_id",
        "encoding",
        "codepage",
    ]
    changed = " OR ".join(f"OLD.{field} IS NOT NEW.{field}" for field in fields)
    schema_editor.execute(
        f"CREATE TRIGGER immutable_print_intent BEFORE UPDATE ON hardware_printjob WHEN {changed} "
        "BEGIN SELECT RAISE(ABORT, 'Print intention immutable'); END"
    )
    schema_editor.execute(
        "CREATE TRIGGER immutable_print_delete BEFORE DELETE ON hardware_printjob "
        "BEGIN SELECT RAISE(ABORT, 'Print history immutable'); END"
    )
    for table in ("hardware_printjob", "hardware_hardwareevent"):
        schema_editor.execute(
            f"CREATE TRIGGER prevent_replace_{table} BEFORE INSERT ON {table} "
            f"WHEN EXISTS (SELECT 1 FROM {table} WHERE id=NEW.id) "
            "BEGIN SELECT RAISE(ABORT, 'Hardware history replacement forbidden'); END"
        )
    for operation in ("UPDATE", "DELETE"):
        schema_editor.execute(
            f"CREATE TRIGGER immutable_hardware_event_{operation.lower()} BEFORE {operation} ON hardware_hardwareevent "
            "BEGIN SELECT RAISE(ABORT, 'Hardware event immutable'); END"
        )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute("DROP TRIGGER IF EXISTS immutable_print_intent")
        schema_editor.execute("DROP TRIGGER IF EXISTS immutable_print_delete")
        for table in ("hardware_printjob", "hardware_hardwareevent"):
            schema_editor.execute(f"DROP TRIGGER IF EXISTS prevent_replace_{table}")
        for operation in ("update", "delete"):
            schema_editor.execute(f"DROP TRIGGER IF EXISTS immutable_hardware_event_{operation}")


class Migration(migrations.Migration):
    dependencies = [
        ("hardware", "0002_printer_terminal_printjob_codepage_printjob_encoding_and_more")
    ]
    operations = [migrations.RunPython(snapshot_and_protect, unprotect)]
