"""Synthetic isolated SQLite benchmark. Never touches an installed company's database."""

import argparse
import json
import multiprocessing
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def writer(database, index, count, ready, start, output):
    os.environ.update(
        BEAUTYTPV_DB=database, BEAUTYTPV_DEBUG="1", DJANGO_SETTINGS_MODULE="config.settings"
    )
    sys.path.insert(0, str(ROOT))
    import django

    django.setup()
    from django.db import connections

    from apps.accounts.models import User
    from apps.catalog.models import CatalogItem
    from apps.pos.services import add_line, checkout, quick_ticket

    actor = User.objects.get(username=f"benchmark-{index}")
    item = CatalogItem.objects.get(name="Servicio sintetico")
    ready.put(index)
    start.wait(30)
    latencies, errors = [], []
    for number in range(count):
        began = time.perf_counter()
        try:
            ticket = quick_ticket(actor)
            add_line(ticket, item, actor)
            checkout(
                ticket,
                actor,
                [{"method": "CARD", "amount": "12.10", "reference": f"SYNTHETIC-{index}-{number}"}],
                f"benchmark-{index}-{number}",
            )
            latencies.append(time.perf_counter() - began)
        except Exception as error:
            errors.append(type(error).__name__)
    connections.close_all()
    output.put({"latencies": latencies, "errors": errors})


def benchmark(terminals, operations):
    context = multiprocessing.get_context("spawn")
    with tempfile.TemporaryDirectory(prefix="beautytpv-benchmark-") as directory:
        database = str(Path(directory) / "isolated.sqlite3")
        env = {**os.environ, "BEAUTYTPV_DB": database, "BEAUTYTPV_DEBUG": "1"}
        subprocess.run(
            [sys.executable, "manage.py", "migrate", "--noinput"],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
        )
        seed = f"""from apps.accounts.models import User
from apps.core.models import CompanySettings
from apps.catalog.models import CatalogItem
c=CompanySettings.load();c.name='Centro sintetico';c.tax_id='89890001K';c.address='Pruebas';c.producer_name='Productor prueba';c.producer_tax_id='89890001K';c.quick_sale_enabled=True;c.save()
CatalogItem.objects.create(name='Servicio sintetico',price='12.10',tax_rate='21')
for i in range({terminals}): User.objects.create_user(username=f'benchmark-{{i}}')
"""
        subprocess.run(
            [sys.executable, "manage.py", "shell", "-c", seed],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
        )
        ready, output, start = context.Queue(), context.Queue(), context.Event()
        processes = [
            context.Process(target=writer, args=(database, index, operations, ready, start, output))
            for index in range(terminals)
        ]
        try:
            for process in processes:
                process.start()
            for _ in processes:
                ready.get(timeout=45)
            began = time.perf_counter()
            start.set()
            records = [output.get(timeout=180) for _ in processes]
            elapsed = time.perf_counter() - began
            for process in processes:
                process.join(10)
                if process.exitcode != 0:
                    raise RuntimeError("Worker no completo el ensayo.")
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(10)
        timings = sorted(value for record in records for value in record["latencies"])
        errors = [error for record in records for error in record["errors"]]
        verification = """import json
from apps.pos.models import Sale
from apps.billing.models import Invoice
from apps.verifactu.services import verify_chain
print(json.dumps({'sales':Sale.objects.count(),'invoices':Invoice.objects.count(),'chain':verify_chain()}))
"""
        check = subprocess.run(
            [sys.executable, "manage.py", "shell", "-c", verification],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        integrity = json.loads(check.stdout.strip().splitlines()[-1])
        if (
            not integrity["chain"]
            or integrity["sales"] != len(timings)
            or integrity["invoices"] != len(timings)
        ):
            raise RuntimeError("Integridad o reconciliacion de ventas del ensayo no valida.")
        p95 = timings[min(len(timings) - 1, int(len(timings) * 0.95))] if timings else None
        return {
            "terminals": terminals,
            "operations_per_terminal": operations,
            "successful": len(timings),
            "errors": errors,
            "elapsed_seconds": round(elapsed, 4),
            "median_seconds": round(statistics.median(timings), 4) if timings else None,
            "p95_seconds": round(p95, 4) if p95 is not None else None,
            "integrity": integrity,
            "internal_review_trigger": bool(errors or p95 is None or p95 > 2),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminals", type=int, nargs="+", default=[1, 3, 6])
    parser.add_argument("--operations", type=int, default=10)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not 1 <= args.operations <= 100 or any(not 1 <= n <= 12 for n in args.terminals):
        parser.error("Use 1-12 terminales y 1-100 operaciones sinteticas.")
    results = []
    for terminals in args.terminals:
        result = benchmark(terminals, args.operations)
        results.append(result)
        print(json.dumps(result), flush=True)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {"kind": "SYNTHETIC_LOCAL_NOT_CAPACITY_CERTIFICATION", "results": results}, indent=2
        ),
        encoding="utf-8",
    )
