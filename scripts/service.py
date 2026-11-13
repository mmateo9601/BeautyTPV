import argparse
import os
import subprocess
import sys

from runtime import ROOT, load_instance


def main():
    parser = argparse.ArgumentParser(description="Servicio BeautyTPV con bloqueo de mantenimiento")
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

    from apps.support.operations import service_lock

    processes = []
    with service_lock(settings.DATABASES["default"]["NAME"]):
        try:
            # Workers share lifecycle of service; external workers must be stopped before restore.
            for command in ["hardware_worker", "operations_worker"]:
                if (
                    ROOT
                    / "apps"
                    / ("hardware" if command == "hardware_worker" else "support")
                    / "management"
                    / "commands"
                    / (command + ".py")
                ).exists():
                    processes.append(
                        subprocess.Popen(
                            [sys.executable, str(ROOT / "manage.py"), command], cwd=ROOT
                        )
                    )
            from django.core.wsgi import get_wsgi_application
            from waitress import serve

            application = get_wsgi_application()
            if args.development:
                from django.contrib.staticfiles.handlers import StaticFilesHandler

                application = StaticFilesHandler(application)
            serve(application, host=args.host, port=args.port, threads=4)
        finally:
            for process in processes:
                process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()
