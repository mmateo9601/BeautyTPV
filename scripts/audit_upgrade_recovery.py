"""Reproducible 4ce821e -> working tree upgrade and real CLI recovery on synthetic data."""

import argparse
import io
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, root, env):
    result = subprocess.run(
        [sys.executable, *map(str, arguments)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if result.returncode:
        raise RuntimeError(f"{arguments[0]} failed ({result.returncode}): {result.stderr[-1500:]}")
    return result.stdout


def inspect_database(path):
    with closing(sqlite3.connect(path)) as database:
        return {
            "sales": database.execute("SELECT COUNT(*) FROM pos_sale").fetchone()[0],
            "invoices": database.execute("SELECT COUNT(*) FROM billing_invoice").fetchone()[0],
            "fingerprints": database.execute(
                "SELECT fingerprint FROM verifactu_fiscalrecord ORDER BY id"
            ).fetchall(),
            "integrity": database.execute("PRAGMA integrity_check").fetchone()[0],
        }


def execute():
    with tempfile.TemporaryDirectory(prefix="beautytpv-upgrade-audit-") as temporary:
        directory = Path(temporary)
        reference = directory / "reference"
        reference.mkdir()
        archive = subprocess.run(
            ["git", "archive", "--format=zip", "4ce821e"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        with zipfile.ZipFile(io.BytesIO(archive)) as source:
            source.extractall(reference)
        database = directory / "legacy.sqlite3"
        env = {**os.environ, "BEAUTYTPV_DB": str(database), "BEAUTYTPV_DEBUG": "1"}
        run([reference / "manage.py", "migrate", "--noinput"], reference, env)
        run([reference / "manage.py", "bootstrap"], reference, env)
        seed = """from apps.accounts.models import User
from apps.core.models import CompanySettings
from apps.layout.models import Station
from apps.catalog.models import CatalogItem
from apps.pos.services import open_ticket,add_line,checkout,cancel_ticket
actor=User.objects.create_user(username='synthetic-upgrade',role='MANAGER')
c=CompanySettings.load();c.name='Centro sintetico';c.tax_id='89890001K';c.address='Pruebas';c.producer_name='Productor sintetico';c.producer_tax_id='89890001K';c.save()
item=CatalogItem.objects.create(name='Servicio sintetico',price='12.10',tax_rate='21')
ticket=open_ticket(Station.objects.get(code='A1'),actor);add_line(ticket,item,actor)
checkout(ticket,actor,[{'method':'CARD','amount':'12.10','reference':'SYNTHETIC-CONFIRMATION'}],'upgrade-idempotency')
cancelled=open_ticket(Station.objects.get(code='A2'),actor);cancel_ticket(cancelled,actor)
opened=open_ticket(Station.objects.get(code='A3'),actor);add_line(opened,item,actor)
"""
        run([reference / "manage.py", "shell", "-c", seed], reference, env)
        before = inspect_database(database)
        run([ROOT / "manage.py", "migrate", "--noinput"], ROOT, env)
        after = inspect_database(database)
        if before != after:
            raise AssertionError("Upgrade changed immutable transaction evidence")
        verify = """import json
from apps.pos.models import OpenTicket
from apps.verifactu.services import verify_chain
t=OpenTicket.objects.get(station__code='A2')
assert t.cancelled_at is not None and t.cancelled_by_id is not None
assert OpenTicket.objects.get(station__code='A3').lines.count()==1
assert verify_chain()
print(json.dumps({'cancellation_backfilled':True,'open_account_persisted':True,'chain':True}))
"""
        outcome = json.loads(
            run([ROOT / "manage.py", "shell", "-c", verify], ROOT, env).strip().splitlines()[-1]
        )
        config = directory / "instance.json"
        config.write_text(
            json.dumps(
                {
                    "BEAUTYTPV_DB": str(database),
                    "BEAUTYTPV_DEBUG": "1",
                    "BEAUTYTPV_SECRET_KEY": secrets.token_urlsafe(64),
                    "BEAUTYTPV_BACKUP_KEY": Fernet.generate_key().decode(),
                    "BEAUTYTPV_BACKUP_DIR": str(directory / "backups"),
                }
            ),
            encoding="utf-8",
        )
        backup = directory / "verified.btpv"
        run([ROOT / "scripts/backup.py", "--instance", config, "--output", backup], ROOT, env)
        run(
            [
                ROOT / "scripts/restore.py",
                "--instance",
                config,
                "--archive",
                backup,
                "--offline",
                "--confirm",
                "RESTORE OFFLINE",
            ],
            ROOT,
            env,
        )
        if (
            inspect_database(database) != after
            or not Path(str(database) + ".fiscal-restore-hold").exists()
        ):
            raise AssertionError("Recovery evidence or hold missing")
        fresh = directory / "new-instance"
        run(
            [
                ROOT / "scripts/install.py",
                "--instance-dir",
                fresh,
                "--skip-dependencies",
                "--no-user",
            ],
            ROOT,
            {key: value for key, value in env.items() if key != "BEAUTYTPV_DB"},
        )
        with closing(sqlite3.connect(fresh / "db.sqlite3")) as connection:
            no_defaults = (
                connection.execute("SELECT COUNT(*) FROM accounts_user").fetchone()[0] == 0
            )
        return {
            "kind": "SYNTHETIC_DATA_REAL_PROCESSES_AND_CLI",
            "reference": "4ce821e",
            "upgrade": "PASS",
            "before": before,
            "after": after,
            **outcome,
            "backup_cli": "PASS",
            "restore_cli": "PASS",
            "restore_hold": True,
            "clean_instance_install": "PASS",
            "no_default_users": no_defaults,
            "dependencies": "Preinstalled environment; no clean-machine or physical-device claim",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = execute()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence))
