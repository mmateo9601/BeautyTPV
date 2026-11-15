"""Independent Windows launcher safety checks using temporary DEMO instances.

No production database or LOCALAPPDATA instance is used. Process termination in
test cleanup only targets the particular sentinel process created by this test.
The coordinator separately records the real GUI/HTTP/start/stop smoke test.
"""

import json
import os
import secrets
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from scripts.demo_config import read_configuration

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "windows_demo.py"


@pytest.mark.parametrize("filename", ["demo.sqlite3", "credenciales-demo.txt"])
def test_configuration_guard_rejects_hardlinks_before_any_write(tmp_path, filename):
    directory = tmp_path / "guard-demo"
    directory.mkdir()
    config = {
        "kind": "BeautyTPV-DEMO",
        "version": 1,
        "secret_key": secrets.token_urlsafe(64),
        "backup_key": Fernet.generate_key().decode("ascii"),
    }
    (directory / "config.json").write_text(json.dumps(config), encoding="utf-8")
    external = tmp_path / "unrelated-file"
    external.write_bytes(b"Unrelated data must never be overwritten")
    os.link(external, directory / filename)
    with pytest.raises(ValueError):
        read_configuration(directory)
    assert external.read_bytes() == b"Unrelated data must never be overwritten"


def invoke(action, directory, *extra, environment=None):
    return subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            action,
            "--instance-dir",
            str(directory),
            "--no-gui",
            "--no-browser",
            *extra,
        ],
        cwd=ROOT,
        env=environment or os.environ.copy(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )


@pytest.fixture
def private_demo(tmp_path):
    directory = tmp_path / "BeautyTPV-DEMO"
    result = invoke("setup", directory)
    # Do not include captured stdout in failures: future UI changes must never
    # accidentally publish a generated password in a JUnit assertion message.
    assert result.returncode == 0, "Temporary DEMO setup failed; inspect local sanitized log."
    assert (directory / "config.json").is_file()
    assert (directory / "demo.sqlite3").is_file()
    return directory


def test_setup_refuses_an_unrelated_existing_configuration(tmp_path):
    directory = tmp_path / "unrelated-installation"
    directory.mkdir()
    configuration = directory / "config.json"
    original = b'{"kind":"REAL-INSTALLATION","version":1}'
    configuration.write_bytes(original)
    sentinel = directory / "main.sqlite3"
    sentinel.write_bytes(b"DO NOT TOUCH: unrelated database")
    result = invoke("setup", directory)
    assert result.returncode != 0
    assert configuration.read_bytes() == original
    assert sentinel.read_bytes() == b"DO NOT TOUCH: unrelated database"
    assert not (directory / "demo.sqlite3").exists()


def test_reset_requires_explicit_confirmation_without_mutating_instance(tmp_path):
    directory = tmp_path / "reset-candidate"
    directory.mkdir()
    sentinel = directory / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    result = invoke("reset", directory, "--confirm", "WRONG CONFIRMATION")
    assert result.returncode != 0
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert not (directory / "demo.sqlite3").exists()


def test_setup_does_not_follow_a_database_inherited_from_environment(tmp_path):
    directory = tmp_path / "isolated-demo"
    main = tmp_path / "principal.sqlite3"
    original = b"Unrelated non-SQLite sentinel must remain byte-identical"
    main.write_bytes(original)
    environment = {
        **os.environ,
        "BEAUTYTPV_DB": str(main),
        "BEAUTYTPV_DEBUG": "1",
        "BEAUTYTPV_FISCAL_ENVIRONMENT": "PRODUCTION",
        "BEAUTYTPV_AEAT_CERTIFICATE": "unrelated-certificate.pem",
        "BEAUTYTPV_AEAT_PRIVATE_KEY": "unrelated-private-key.pem",
        "DJANGO_SETTINGS_MODULE": "nonexistent.production_settings",
    }
    result = invoke("setup", directory, environment=environment)
    assert result.returncode == 0, "DEMO must sanitize inherited settings before setup."
    assert main.read_bytes() == original
    assert (directory / "demo.sqlite3").is_file()


def test_repeated_setup_preserves_the_existing_demo_database(private_demo):
    import sqlite3

    with closing(sqlite3.connect(private_demo / "demo.sqlite3")) as connection:
        with connection:
            connection.execute("CREATE TABLE qa_demo_sentinel (value TEXT)")
            connection.execute("INSERT INTO qa_demo_sentinel VALUES ('persistent')")
    result = invoke("setup", private_demo)
    assert result.returncode == 0
    with closing(sqlite3.connect(private_demo / "demo.sqlite3")) as connection:
        assert connection.execute("SELECT value FROM qa_demo_sentinel").fetchone() == (
            "persistent",
        )


def test_setup_rejects_a_hardlinked_database_before_migrating_it(private_demo, tmp_path):
    import sqlite3

    external = tmp_path / "unrelated-main.sqlite3"
    with closing(sqlite3.connect(external)) as connection:
        with connection:
            connection.execute("CREATE TABLE unrelated_history (value TEXT)")
            connection.execute("INSERT INTO unrelated_history VALUES ('preserve')")
    original = external.read_bytes()
    database = private_demo / "demo.sqlite3"
    database.unlink()
    os.link(external, database)
    assert external.stat().st_nlink == 2
    result = invoke("setup", private_demo)
    assert result.returncode != 0
    assert external.read_bytes() == original, "Reject links before any migration mutates SQLite."


@pytest.mark.skipif(os.name != "nt", reason="Windows process creation identity and named events")
def test_stale_state_cannot_stop_an_unrelated_python_process(private_demo):
    import json

    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        state = {
            "pid": process.pid,
            "created_at": 1,
            "token": "a" * 64,
        }
        (private_demo / "server.json").write_text(json.dumps(state), encoding="utf-8")
        invoke("stop", private_demo)
        assert process.poll() is None, "Stop must never terminate an unrelated Python process."
    finally:
        process.terminate()
        process.wait(timeout=10)
