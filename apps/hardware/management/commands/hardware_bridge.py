import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.utils.crypto import constant_time_compare

from apps.hardware.services import process_job


class Command(BaseCommand):
    help = "Bridge HTTP loopback autenticado: solo procesa IDs existentes en la cola local."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8766)

    def handle(self, *args, **options):
        from django.conf import settings

        from apps.support.operations import service_lock

        with service_lock(settings.DATABASES["default"]["NAME"]):
            return self.run_locked(*args, **options)

    def run_locked(self, *args, **options):
        token = os.getenv("BEAUTYTPV_BRIDGE_TOKEN", "")
        if len(token) < 32:
            raise CommandError(
                "BEAUTYTPV_BRIDGE_TOKEN debe contener al menos 32 caracteres aleatorios"
            )

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                auth = self.headers.get("Authorization", "")
                if not constant_time_compare(auth, "Bearer " + token):
                    self.send_error(403)
                    return
                match = re.fullmatch(r"/jobs/([1-9][0-9]*)", self.path)
                # No raw bytes, shell, arbitrary device addresses or commands accepted.
                if not match or int(self.headers.get("Content-Length", "0")) != 0:
                    self.send_error(400)
                    return
                close_old_connections()
                try:
                    result = process_job(int(match.group(1)))
                    body = b'{"sent":true}' if result else b'{"sent":false}'
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                finally:
                    close_old_connections()

            def log_message(self, *args):
                pass  # No tokens or document data in HTTP access logs.

        server = ThreadingHTTPServer(("127.0.0.1", options["port"]), Handler)
        self.stdout.write("Bridge loopback listo; no exponer directamente a LAN")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
