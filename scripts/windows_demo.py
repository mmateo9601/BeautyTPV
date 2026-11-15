"""Windows desktop lifecycle for the isolated BeautyTPV DEMO (no production data)."""

import argparse
import contextlib
import ctypes
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.demo_config import (  # noqa: E402
    KIND,
    demo_directory,
    demo_environment,
    read_configuration,
    secure_directory,
)

URL = "http://127.0.0.1:8000"


def process_created(pid):
    if os.name != "nt" or type(pid) is not int or pid <= 0:
        return None
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        creation, end, system, user = (wintypes.FILETIME() for _ in range(4))
        code = wintypes.DWORD()
        if (
            not kernel.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(end),
                ctypes.byref(system),
                ctypes.byref(user),
            )
            or not kernel.GetExitCodeProcess(handle, ctypes.byref(code))
            or code.value != 259
        ):
            return None
        return (creation.dwHighDateTime << 32) | creation.dwLowDateTime
    finally:
        kernel.CloseHandle(handle)


def process_descends_from(pid, ancestor):
    """Python's Windows venv redirector may host a child interpreter PID."""
    if type(pid) is not int or pid <= 0:
        return False
    if pid == ancestor:
        return True
    if os.name != "nt":
        return False
    from ctypes import wintypes

    class Entry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("pid", wintypes.DWORD),
            ("heap", ctypes.c_size_t),
            ("module", wintypes.DWORD),
            ("threads", wintypes.DWORD),
            ("parent", wintypes.DWORD),
            ("priority", wintypes.LONG),
            ("flags", wintypes.DWORD),
            ("exe", wintypes.WCHAR * 260),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle in (None, ctypes.c_void_p(-1).value):
        return False
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        parents = {}
        found = kernel.Process32FirstW(handle, ctypes.byref(entry))
        while found:
            parents[entry.pid] = entry.parent
            found = kernel.Process32NextW(handle, ctypes.byref(entry))
        current = pid
        for _ in range(8):
            current = parents.get(current)
            if current == ancestor:
                return True
            if not current:
                break
        return False
    finally:
        kernel.CloseHandle(handle)


@contextlib.contextmanager
def launch_lock(directory):
    if os.name != "nt":
        raise ValueError("El lanzador de escritorio requiere Windows 10/11.")
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    name = (
        "Local\\BeautyTPV-DEMO-launch-"
        + hashlib.sha256(os.path.normcase(str(directory)).encode()).hexdigest()
    )
    handle = kernel.CreateMutexW(None, False, name)
    if not handle:
        raise ValueError("No se pudo bloquear el arranque DEMO.")
    acquired = False
    try:
        result = kernel.WaitForSingleObject(handle, 120000)
        if result not in (0, 0x80):
            raise ValueError("Hay otra preparacion DEMO en curso. Espere y vuelva a intentarlo.")
        acquired = True
        yield
    finally:
        if acquired:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


def dependencies():
    if sys.version_info < (3, 12):
        raise ValueError("BeautyTPV requiere Python 3.12 o posterior.")
    import importlib

    for name in (
        "django",
        "waitress",
        "whitenoise",
        "cryptography",
        "PIL",
        "lxml",
        "qrcode",
        "reportlab",
    ):
        try:
            importlib.import_module(name)
        except ImportError as error:
            raise ValueError(
                "Faltan dependencias. Instale requirements.lock.txt en .venv; consulte GUIA_WINDOWS_DEMO.md."
            ) from error
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    if result.returncode:
        raise ValueError("Dependencias incompatibles. Revise .venv con pip check y la guia DEMO.")


def command(directory, arguments):
    directory = demo_directory(directory)
    with (directory / "preparacion.log").open("a", encoding="utf-8") as logs:
        result = subprocess.run(
            [sys.executable, str(ROOT / "manage.py"), *arguments],
            cwd=ROOT,
            env=demo_environment(directory),
            stdout=logs,
            stderr=subprocess.STDOUT,
            timeout=180,
        )
    if result.returncode:
        raise ValueError(
            "La preparacion DEMO fallo. Revise preparacion.log en la carpeta DEMO; no se ha usado la base principal."
        )


def seed(directory, rotate=False):
    code = (
        "from scripts.demo_seed import prepare_demo; from scripts.demo_config import write_credentials; from django.conf import settings; write_credentials(settings.DEMO_DIRECTORY,prepare_demo(rotate_users="
        + repr(rotate)
        + "))"
    )
    command(directory, ["shell", "-c", code])


def setup_demo(directory):
    from cryptography.fernet import Fernet

    directory = demo_directory(directory)
    if not (directory / "config.json").exists():
        if directory.exists() and any(directory.iterdir()):
            raise ValueError("La carpeta no esta vacia y no tiene marcador DEMO. No se modifica.")
        secure_directory(directory)
        values = {
            "kind": KIND,
            "version": 1,
            "secret_key": secrets.token_urlsafe(64),
            "backup_key": Fernet.generate_key().decode(),
        }
        with (directory / "config.json").open("x", encoding="utf-8") as stream:
            json.dump(values, stream, indent=2)
    read_configuration(directory)
    command(directory, ["migrate", "--noinput"])
    command(directory, ["bootstrap"])
    seed(directory)
    command(directory, ["check"])
    command(directory, ["collectstatic", "--noinput"])


def read_state(directory):
    path = directory / "server.json"
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(state, dict)
        or type(state.get("pid")) is not int
        or type(state.get("created_at")) is not int
        or not isinstance(state.get("token"), str)
        or len(state["token"]) != 64
        or any(c not in "0123456789abcdef" for c in state["token"])
    ):
        raise ValueError("Estado DEMO invalido. No se detiene ningun proceso; revise server.json.")
    return state


def ready(state):
    if process_created(state["pid"]) != state["created_at"]:
        return False
    request = urllib.request.Request(
        URL + "/__demo_ready__", headers={"X-BeautyTPV-Demo": state["token"]}
    )
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=2) as response:
            data = json.load(response)
        return (
            data.get("demo") is True
            and process_descends_from(data.get("pid"), state["pid"])
            and data.get("mode") == "TEST"
            and data.get("identity") == hashlib.sha256(state["token"].encode()).hexdigest()
        )
    except (OSError, ValueError, urllib.error.URLError):
        return False


def port_available():
    try:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 8000))
        return True
    except OSError:
        return False


def start_demo(directory):
    directory = demo_directory(directory)
    new = not (directory / "config.json").exists()
    if not new:
        read_configuration(directory)
        current = read_state(directory)
        if current and ready(current):
            return "ALREADY_RUNNING", False
        if current and process_created(current["pid"]) == current["created_at"]:
            raise ValueError(
                "El proceso DEMO sigue activo pero no responde. Use Detener BeautyTPV DEMO y revise demo-server.log."
            )
    if not port_available():
        raise ValueError(
            "El puerto 127.0.0.1:8000 esta ocupado por otro proceso. No se cierra ni modifica ese proceso."
        )
    if new:
        setup_demo(directory)
    else:
        if not (directory / "demo.sqlite3").is_file():
            raise ValueError(
                "Falta demo.sqlite3 de una DEMO configurada. Use Preparar o Reinicializar DEMO; no se crea otra base silenciosamente."
            )
        command(directory, ["migrate", "--noinput"])
        command(directory, ["check"])
        command(directory, ["collectstatic", "--noinput"])
    token = secrets.token_hex(32)
    executable = Path(sys.executable).with_name("pythonw.exe")
    if not executable.exists():
        executable = Path(sys.executable)
    with (directory / "demo-server.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                str(executable),
                str(ROOT / "scripts/demo_server.py"),
                "--instance-dir",
                str(directory),
                "--token",
                token,
            ],
            cwd=ROOT,
            env=demo_environment(directory),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    state = {"pid": process.pid, "created_at": process_created(process.pid), "token": token}
    if state["created_at"] is None:
        raise ValueError(
            "No se pudo verificar la identidad del proceso DEMO. Revise demo-server.log."
        )
    (directory / "server.json").write_text(json.dumps(state), encoding="utf-8")
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if ready(state):
            return "STARTED", new
        if process.poll() is not None:
            raise ValueError(
                "El servidor DEMO no pudo arrancar. Revise demo-server.log; no se ha cerrado ningun proceso ajeno."
            )
        time.sleep(0.25)
    # Cooperative stop only for the process we have identified, never taskkill.
    try:
        stop_demo(directory)
    except (ValueError, OSError):
        pass
    raise ValueError(
        "La DEMO no respondio a tiempo. Revise demo-server.log y use Detener antes de reintentar."
    )


def stop_demo(directory):
    read_configuration(directory)
    state = read_state(directory)
    if not state:
        return "ALREADY_STOPPED"
    if process_created(state["pid"]) != state["created_at"]:
        # Stale PID is not authority to signal or terminate anything.
        (directory / "server.json").unlink()
        return "STALE_STATE_REMOVED"
    from scripts.demo_server import WindowsEvent

    with WindowsEvent(state["token"], create=False) as event:
        event.set()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process_created(state["pid"]) != state["created_at"]:
            (directory / "server.json").unlink(missing_ok=True)
            return "STOPPED"
        time.sleep(0.2)
    raise ValueError(
        "La parada DEMO no ha terminado. Revise demo-server.log. No se fuerza el cierre de procesos Python."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=["setup", "start", "stop", "status", "credentials", "reset", "rotate-users"],
    )
    parser.add_argument("--instance-dir")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    try:
        directory = demo_directory(args.instance_dir)
        if args.action in ("reset", "rotate-users"):
            required = "REINICIAR DEMO" if args.action == "reset" else "CAMBIAR USUARIOS DEMO"
            if args.no_gui:
                if args.confirm != required:
                    raise ValueError("Confirmacion obligatoria: " + required)
            else:
                from tkinter import messagebox

                if not messagebox.askyesno(
                    "BeautyTPV DEMO",
                    "Esta accion afecta exclusivamente a la DEMO. Se archivara la DEMO actual o se cambiaran sus credenciales. ¿Continuar?",
                ):
                    return 0
        with launch_lock(directory):
            if args.action == "stop":
                result = (
                    stop_demo(directory)
                    if (directory / "config.json").exists()
                    else "ALREADY_STOPPED"
                )
            elif args.action == "status":
                read_configuration(directory)
                state = read_state(directory)
                result = "RUNNING" if state and ready(state) else "STOPPED"
            elif args.action == "credentials":
                read_configuration(directory)
                if not (directory / "credenciales-demo.txt").exists():
                    raise ValueError(
                        "No existe el archivo de credenciales. Use Cambiar usuarios DEMO de forma explicita."
                    )
                if not args.no_gui:
                    os.startfile(directory / "credenciales-demo.txt")
                result = "CREDENTIALS_AVAILABLE"
            else:
                dependencies()
                if args.action in ("reset", "rotate-users"):
                    read_configuration(directory)
                    stop_demo(directory)
                    if args.action == "reset":
                        archived = directory.with_name(
                            directory.name
                            + "-archivada-"
                            + time.strftime("%Y%m%d-%H%M%S")
                            + "-"
                            + secrets.token_hex(3)
                        )
                        if archived.parent != directory.parent or archived.exists():
                            raise ValueError("Destino de archivo DEMO no valido.")
                        directory.rename(archived)
                        setup_demo(directory)
                    else:
                        seed(directory, rotate=True)
                    result = "DEMO_RECONFIGURED"
                elif args.action == "setup":
                    state = read_state(directory) if (directory / "config.json").exists() else None
                    if state and process_created(state["pid"]) == state["created_at"]:
                        raise ValueError("Detenga la DEMO antes de prepararla.")
                    setup_demo(directory)
                    result = "PREPARED"
                else:
                    result, new = start_demo(directory)
                    if not args.no_browser:
                        import webbrowser

                        webbrowser.open(URL + "/acceso/")
                    if new and not args.no_gui:
                        from tkinter import messagebox

                        messagebox.showinfo(
                            "Usuarios BeautyTPV DEMO",
                            "Se han generado cuatro usuarios con credenciales privadas diferentes. Se abrira el archivo local de credenciales. Guardelo de forma segura; solo son para esta DEMO.",
                        )
                        os.startfile(directory / "credenciales-demo.txt")
        if args.no_gui:
            print(result)
        elif args.action not in ("start", "credentials", "stop"):
            from tkinter import messagebox

            messagebox.showinfo("BeautyTPV DEMO", "Operacion completada: " + result)
        return 0
    except Exception as error:
        message = (
            str(error)
            if isinstance(error, (ValueError, FileNotFoundError))
            else "Operacion DEMO fallida ("
            + type(error).__name__
            + "). Consulte los logs de la carpeta DEMO y GUIA_WINDOWS_DEMO.md."
        )
        if args.no_gui:
            print(message, file=sys.stderr)
        else:
            ctypes.windll.user32.MessageBoxW(
                None, message, "BeautyTPV DEMO - No se pudo completar", 0x10
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
