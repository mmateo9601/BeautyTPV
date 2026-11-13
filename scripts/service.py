import argparse
import os
import subprocess
import sys
import threading

try:
    from scripts.runtime import ROOT, load_instance
except ModuleNotFoundError:
    from runtime import ROOT, load_instance


def supervise_workers(workers, stop_event, on_failure, report, interval=2):
    """Do not leave a healthy-looking web service after a required child dies."""
    try:
        while not stop_event.is_set():
            for name, process in workers:
                code = process.poll()
                report(
                    name,
                    "RUNNING" if code is None else "FAILED",
                    "" if code is None else "EXIT_" + str(code),
                    process.pid,
                )
                if code is not None:
                    on_failure(name, code)
                    return
            report("service", "RUNNING", "", os.getpid())
            stop_event.wait(interval)
    except Exception as error:
        on_failure("supervisor", type(error).__name__)


def close_server(server):
    from waitress import wasyncore

    dispatcher = getattr(server, "task_dispatcher", None)
    if dispatcher is not None:
        dispatcher.shutdown()
    server.close()
    mapping = getattr(server, "_map", getattr(server, "map", None))
    if mapping is not None:
        wasyncore.close_all(mapping)


def main():
    parser = argparse.ArgumentParser(
        description="Servicio BeautyTPV con supervisión y bloqueo de mantenimiento"
    )
    parser.add_argument("--instance", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    load_instance(args.instance)
    if args.development:
        os.environ["BEAUTYTPV_DEBUG"] = "1"
    import django

    django.setup()
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.db import close_old_connections
    from waitress import create_server

    from apps.support.operations import service_lock
    from apps.support.scheduler import heartbeat

    workers, failures = [], []
    stop_event = threading.Event()
    monitor = server = None
    with service_lock(settings.DATABASES["default"]["NAME"]):
        try:
            application = get_wsgi_application()
            if args.development:
                from django.contrib.staticfiles.handlers import StaticFilesHandler

                application = StaticFilesHandler(application)
            server = create_server(
                application, host=args.host, port=args.port, threads=4, asyncore_loop_timeout=1
            )
            for name in ["hardware_worker", "operations_worker"]:
                process = subprocess.Popen(
                    [sys.executable, str(ROOT / "manage.py"), name], cwd=ROOT
                )
                workers.append((name, process))

            def failed(name, code):
                failures.append((name, code))
                close_server(server)

            def report(name, state, error, pid):
                close_old_connections()
                heartbeat(name, state, error, pid)

            monitor = threading.Thread(
                target=supervise_workers,
                args=(workers, stop_event, failed, report),
                daemon=True,
                name="beautytpv-supervisor",
            )
            monitor.start()
            server.run()
        finally:
            stop_event.set()
            if monitor is not None:
                monitor.join(timeout=5)
            if server is not None:
                close_server(server)
            for _, process in workers:
                if process.poll() is None:
                    process.terminate()
            for _, process in workers:
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            heartbeat(
                "service", "FAILED" if failures else "STOPPED", "WORKER_EXIT" if failures else ""
            )
    if failures:
        raise RuntimeError(
            "Worker requerido detenido; servicio cerrado para evitar operativa parcial."
        )


if __name__ == "__main__":
    main()
