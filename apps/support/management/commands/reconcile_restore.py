import getpass
import hashlib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.accounts.permissions import require_role
from apps.accounts.services import authenticate_local
from apps.audit.services import record
from apps.support.operations import exclusive_operation, hold_path
from apps.verifactu.services import verify_chain


class Command(BaseCommand):
    help = "Retirar hold SOLO tras conciliar registros locales y AEAT; guarda hash de evidencia externa"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--evidence", required=True)
        parser.add_argument("--confirm", required=True)

    def handle(self, *args, **options):
        if options["confirm"] != "RECONCILED WITH AEAT":
            raise CommandError("Confirmación inválida.")
        evidence = Path(options["evidence"])
        if not evidence.is_file() or not evidence.read_bytes():
            raise CommandError("Aporte informe de conciliación no vacío.")
        actor = authenticate_local(
            options["username"],
            getpass.getpass("Contraseña Superadmin: "),
            "offline",
            password=True,
        )
        require_role(actor, "SUPERADMIN")
        database = settings.DATABASES["default"]["NAME"]
        with exclusive_operation(database):
            if (
                connection.cursor().execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                or not verify_chain()
            ):
                raise CommandError("Integridad/cadena inválida.")
            marker = hold_path(database)
            if not marker.exists():
                raise CommandError("No hay retención de restauración activa.")
            record(
                actor,
                "restore.reconciled",
                metadata={"sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()},
            )
            marker.unlink()
        self.stdout.write(
            "Retención retirada por Superadmin tras declaración de conciliación; evidencia externa no validada automáticamente."
        )
