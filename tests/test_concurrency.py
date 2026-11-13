"""E02/E05/E13 run independent OS processes against a local SQLite file.

No Django transaction fixture or flush is used: issued-record protection remains active.
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "tests/e2e/sqlite_process.py"


def process_env(database):
    return {
        **os.environ,
        "BEAUTYTPV_DB": str(database),
        "BEAUTYTPV_DEBUG": "1",
        "BEAUTYTPV_TEST_PROCESS": "1",
    }


def command(database, data):
    result = subprocess.run(
        [sys.executable, str(DRIVER), json.dumps(data)],
        cwd=ROOT,
        env=process_env(database),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.stdout.strip(), result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    return result.returncode, payload


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    database = tmp_path_factory.mktemp("sqlite-process-baseline") / "baseline.sqlite3"
    code, result = command(database, {"action": "seed"})
    assert code == 0 and result["seeded"], result
    return database


@pytest.fixture
def database(baseline, tmp_path):
    target = tmp_path / "isolated.sqlite3"
    with sqlite3.connect(baseline) as source, sqlite3.connect(target) as destination:
        source.backup(destination)
    return target


def concurrent_checkouts(database, requests, tmp_path):
    gate = tmp_path / "start-checkout"
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                str(DRIVER),
                json.dumps({"action": "checkout", "gate": str(gate), **data}),
            ],
            cwd=ROOT,
            env=process_env(database),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        for data in requests
    ]
    # All start against the same gate; no backend serialization is provided by the test.
    time.sleep(0.5)
    started = time.monotonic()
    gate.touch()
    results = []
    try:
        for process in processes:
            stdout, stderr = process.communicate(timeout=60)
            assert stdout.strip(), stderr
            results.append((process.returncode, json.loads(stdout.strip().splitlines()[-1])))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
    return results, time.monotonic() - started


def test_e02_accounts_survive_process_restart(database):
    code, first = command(database, {"action": "open", "station": "A1", "add": True})
    assert code == 0
    code, second = command(database, {"action": "open", "station": "A2"})
    assert code == 0 and first["ticket"] != second["ticket"]
    code, reopened = command(database, {"action": "open", "station": "A1"})
    assert code == 0 and reopened["ticket"] == first["ticket"]
    code, persisted = command(database, {"action": "inspect"})
    assert code == 0
    assert persisted["tickets"]["A1"]["total"] == "12.10"
    assert persisted["tickets"]["A1"]["lines"] == 1
    assert persisted["tickets"]["A2"]["total"] == "0.00"


def test_e05_two_terminals_same_idempotency_key_one_sale(database, tmp_path):
    _, ticket = command(database, {"action": "open", "station": "A1", "add": True})
    request = {"ticket": ticket["ticket"], "key": "concurrent-same-key"}
    results, elapsed = concurrent_checkouts(database, [request, request], tmp_path)
    assert all(code == 0 for code, _ in results), results
    assert len({result["sale"] for _, result in results}) == 1
    _, state = command(database, {"action": "inspect"})
    assert state["sales"] == state["records"] == state["print_jobs"] == 1
    assert state["chain_valid"]
    assert elapsed < 60


def test_e05_different_keys_do_not_double_charge_ticket(database, tmp_path):
    _, ticket = command(database, {"action": "open", "station": "A1", "add": True})
    requests = [{"ticket": ticket["ticket"], "key": f"different-{index}"} for index in range(2)]
    results, _ = concurrent_checkouts(database, requests, tmp_path)
    assert sum(code == 0 for code, _ in results) == 1, results
    assert [value["type"] for code, value in results if code != 0] == ["ValidationError"]
    _, state = command(database, {"action": "inspect"})
    assert state["sales"] == state["records"] == state["print_jobs"] == 1


def test_e13_three_terminal_sales_numbering_and_chain(database, tmp_path, record_property):
    requests = []
    for index in range(1, 4):
        code, ticket = command(database, {"action": "open", "station": f"A{index}", "add": True})
        assert code == 0
        requests.append({"ticket": ticket["ticket"], "key": f"terminal-{index}"})
    results, elapsed = concurrent_checkouts(database, requests, tmp_path)
    assert all(code == 0 for code, _ in results), results
    _, state = command(database, {"action": "inspect"})
    assert state["sales"] == state["records"] == state["print_jobs"] == 3
    assert len({tuple(number) for number in state["invoices"]}) == 3
    assert state["chain_valid"]
    assert all(ticket["status"] == "CLOSED" for ticket in state["tickets"].values())
    record_property("three_process_elapsed_seconds", round(elapsed, 3))


def test_e12_restore_real_issued_database_holds_send_and_preserves_idempotency(database, tmp_path):
    from apps.support.operations import create_backup, hold_path, restore_backup

    _, ticket = command(database, {"action": "open", "station": "A1", "add": True})
    request = {"action": "checkout", "ticket": ticket["ticket"], "key": "restore-checkout"}
    code, sale = command(database, request)
    assert code == 0, sale
    key = Fernet.generate_key()
    archive = tmp_path / "issued-encrypted.btpv"
    manifest, _ = create_backup(database, archive, key)
    assert manifest["fiscal_watermarks"]["billing_invoice"] == 1
    assert manifest["fiscal_watermarks"]["verifactu_fiscalrecord"] == 1
    restored = tmp_path / "fresh-installation.sqlite3"
    restore_backup(archive, restored, key, confirmation="RESTORE OFFLINE", offline=True)
    assert hold_path(restored).exists()
    code, state = command(restored, {"action": "inspect"})
    assert code == 0 and state["chain_valid"]
    assert state["sales"] == state["records"] == state["print_jobs"] == 1
    code, blocked = command(restored, {"action": "send_one"})
    assert code == 2 and blocked["type"] == "ValidationError"
    assert "retenida" in blocked["error"]
    code, replay = command(restored, request)
    assert code == 2 and replay["type"] == "ValidationError"
    # The operational hold also blocks idempotent checkout until reconciliation.
    assert hold_path(restored).exists()
    _, final = command(restored, {"action": "inspect"})
    assert final["sales"] == final["records"] == final["print_jobs"] == 1


def test_real_process_death_rolls_back_invoice_sequence_and_spool(database):
    code, opened = command(database, {"action": "open", "station": "A1", "add": True})
    assert code == 0
    assert (
        command(database, {"action": "prepare", "ticket": opened["ticket"]})[1]["status"]
        == "PAYMENT_PENDING"
    )
    process = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            json.dumps(
                {
                    "action": "checkout",
                    "ticket": opened["ticket"],
                    "key": "recover-after-kill",
                    "crash_before_commit": True,
                }
            ),
        ],
        cwd=ROOT,
        env=process_env(database),
        capture_output=True,
        timeout=45,
    )
    assert process.returncode == 91
    code, after = command(database, {"action": "inspect"})
    assert code == 0 and after["sales"] == after["records"] == after["print_jobs"] == 0
    assert after["tickets"]["A1"]["status"] == "PAYMENT_PENDING"
    assert after["tickets"]["A1"]["lines"] == 1
    code, recovered = command(
        database, {"action": "checkout", "ticket": opened["ticket"], "key": "recover-after-kill"}
    )
    assert code == 0
    code, after = command(database, {"action": "inspect"})
    assert code == 0 and after["sales"] == after["records"] == after["print_jobs"] == 1
    assert after["invoices"][0][1] == 1 and after["chain_valid"]
