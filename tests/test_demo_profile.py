"""The explicit offline DEMO must not relax production simulation/fiscal guards."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.test import RequestFactory, override_settings

from apps.hardware.drivers import DriverUnavailable, send, simulator_allowed
from apps.verifactu.services import send_one


@pytest.mark.parametrize(
    "debug,module,flag,allowed",
    [
        (False, "config.settings", False, False),
        (False, "config.settings", True, False),
        (False, "config.demo_settings", True, True),
        (True, "config.settings", False, True),
    ],
)
def test_simulator_only_development_or_explicit_demo(debug, module, flag, allowed):
    with override_settings(
        DEBUG=debug, SETTINGS_MODULE=module, LOCAL_DEMO_ONLY=flag, HARDWARE_SIMULATOR=True
    ):
        assert simulator_allowed() is allowed
        if allowed:
            assert send(SimpleNamespace(connection_type="SIMULATOR"), b"synthetic") == 9
        else:
            with pytest.raises(DriverUnavailable):
                send(SimpleNamespace(connection_type="SIMULATOR"), b"synthetic")


@pytest.mark.parametrize("kind", ["TCP", "USB", "SERIAL"])
def test_demo_never_touches_physical_drivers(kind, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("A physical connection was attempted")

    monkeypatch.setattr("socket.create_connection", unexpected)
    with override_settings(LOCAL_DEMO_ONLY=True):
        with pytest.raises(DriverUnavailable):
            send(SimpleNamespace(connection_type=kind), b"synthetic")


def test_demo_fiscal_hold_blocks_before_database_or_transport(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("An AEAT connection was attempted")

    monkeypatch.setattr("requests.post", unexpected)
    with override_settings(FISCAL_RESTORE_HOLD=True):
        with pytest.raises(ValidationError):
            send_one()


def test_base_production_settings_keep_simulator_and_approval_disabled():
    # Inspect the unchanged production module, independently of pytest's DEBUG.
    from config import settings as production

    assert production.FISCAL_PRODUCTION_APPROVED is False
    assert "LOCAL_DEMO_ONLY" not in vars(production)
    # HTTP-only cookie/SSL exceptions exist in demo_settings, not in this module.
    assert production.SESSION_COOKIE_SECURE == (not production.DEBUG)


def test_request_factory_does_not_enable_demo_by_a_request_header():
    request = RequestFactory().get("/", HTTP_X_BEAUTYTPV_DEMO="true")
    with override_settings(DEBUG=False, HARDWARE_SIMULATOR=True, LOCAL_DEMO_ONLY=False):
        assert request.headers["X-BeautyTPV-Demo"] == "true"
        assert not simulator_allowed()


def test_windows_venv_process_identity_accepts_child_and_rejects_unrelated_process():
    import os
    import subprocess
    import sys

    from scripts.windows_demo import process_created, process_descends_from

    child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(20)"])
    try:
        assert process_created(child.pid) is not None
        assert process_descends_from(child.pid, os.getpid())
        assert not process_descends_from(os.getpid(), child.pid)
    finally:
        # This test closes only the sentinel it just created.
        child.terminate()
        child.wait(timeout=10)
