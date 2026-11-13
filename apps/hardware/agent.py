"""Remote terminal printer agent: HTTPS queue protocol, no shared database.

Run: python -m apps.hardware.agent --server https://tpv.example --terminal 1
Token: BEAUTYTPV_TERMINAL_TOKEN environment variable. Keep the journal outside the repo.
"""

import argparse
import base64
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import requests

from .drivers import DeliveryUnknown, DriverUnavailable, send


def validate_server(server, development_loopback=False):
    address = urlsplit(server)
    if address.username or address.password or address.query or address.fragment:
        raise ValueError("URL de servidor no valida.")
    if address.scheme != "https":
        if not (
            development_loopback
            and address.scheme == "http"
            and address.hostname in ("127.0.0.1", "localhost", "::1")
        ):
            raise ValueError(
                "El agente requiere HTTPS; HTTP solo loopback de desarrollo explicito."
            )
    if not address.hostname:
        raise ValueError("Falta host de servidor.")
    return server.rstrip("/")


def write_journal(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(value, output)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def run_once(session, server, terminal, token, journal, sender=send):
    journal = Path(journal)
    headers = {"Authorization": "Bearer " + token}
    resumed = journal.exists()
    if resumed:
        entry = json.loads(journal.read_text(encoding="utf-8"))
        if entry.get("server") != server or entry.get("terminal") != terminal:
            raise ValueError("El journal pertenece a otra instalacion o terminal.")
        # An interrupted process cannot prove that bytes did not reach the device.
        state = entry.get("status") or "UNKNOWN"
    else:
        response = session.post(
            f"{server}/hardware/bridge/{terminal}/claim/", headers=headers, timeout=(10, 20)
        )
        if response.status_code == 204:
            return None
        response.raise_for_status()
        payload = response.json()
        entry = {
            "server": server,
            "terminal": terminal,
            "job_id": payload["job_id"],
            "lease_token": payload["lease_token"],
            "status": None,
        }
        write_journal(journal, entry)  # Persist intention before any irreversible device IO.
        try:
            printer = SimpleNamespace(**payload["printer"])
            if printer.connection_type == "SIMULATOR":
                raise DriverUnavailable("El agente remoto no simula impresiones.")
            sender(printer, base64.b64decode(payload["payload"], validate=True))
            state = "DONE"
        except DriverUnavailable:
            state = "FAILED"
        except (DeliveryUnknown, Exception):
            state = "UNKNOWN"
        entry["status"] = state
        write_journal(journal, entry)
    response = session.post(
        f"{server}/hardware/bridge/{terminal}/jobs/{entry['job_id']}/ack/",
        headers=headers,
        json={"lease_token": entry["lease_token"], "status": state},
        timeout=(10, 20),
    )
    if response.status_code in (200, 409):
        journal.unlink()
        return state if response.status_code == 200 else "UNKNOWN"
    response.raise_for_status()
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    parser.add_argument("--terminal", required=True, type=int)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--development-loopback", action="store_true")
    args = parser.parse_args()
    server = validate_server(args.server, args.development_loopback)
    token = os.environ.get("BEAUTYTPV_TERMINAL_TOKEN", "")
    if not 32 <= len(token) <= 256:
        raise SystemExit("Configure BEAUTYTPV_TERMINAL_TOKEN externo de 32-256 caracteres.")
    with requests.Session() as session:
        while True:
            try:
                outcome = run_once(session, server, args.terminal, token, args.journal)
                if outcome:
                    print("Entrega:", outcome, flush=True)
            except (requests.RequestException, OSError, ValueError):
                print(
                    "Agente sin confirmacion: revise red/configuracion y journal; no repetir bytes manualmente.",
                    flush=True,
                )
            if args.once:
                return
            time.sleep(max(0.5, args.interval))


if __name__ == "__main__":
    main()
