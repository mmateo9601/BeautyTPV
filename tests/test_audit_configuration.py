import os
import subprocess
import sys
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db.utils import OperationalError
from django.utils import timezone

from apps.core.models import CompanySettings
from apps.support.models import ServiceHeartbeat

pytestmark = pytest.mark.django_db


def test_health_checks_database_and_reports_supervision(client):
    result = client.get("/health/")
    assert result.status_code == 200
    assert result.json()["database"] == "OK"
    assert result.json()["workers"] == "UNSUPERVISED"
    service = ServiceHeartbeat.objects.create(name="service", pid=123, state="RUNNING")
    assert client.get("/health/").status_code == 200
    service.last_seen = timezone.now() - timedelta(minutes=1)
    service.save()
    assert client.get("/health/").status_code == 503
    assert client.post("/health/").status_code == 405


def test_health_database_failure_is_not_a_fake_ok(rf):
    from config.views import health

    with patch(
        "config.views.connection.cursor", side_effect=OperationalError("private internal detail")
    ):
        response = health(rf.get("/health/"))
    assert response.status_code == 503
    assert b"private internal detail" not in response.content


def test_ui_environment_is_company_mode_and_timezone_is_restored(client, settings):
    from config.context_processors import installation

    company = CompanySettings.load()
    company.timezone = "Atlantic/Canary"
    company.save()
    settings.FISCAL_ENVIRONMENT = "PRODUCTION"
    assert installation(None)["fiscal_environment"] == "TEST"
    old_zone = timezone.get_current_timezone_name()
    assert client.get("/acceso/").status_code == 200
    assert timezone.get_current_timezone_name() == old_zone


def test_production_start_without_external_secret_fails_closed():
    environment = {**os.environ, "BEAUTYTPV_DEBUG": "0"}
    environment.pop("BEAUTYTPV_SECRET_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", "import config.settings"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "BEAUTYTPV_SECRET_KEY" in result.stderr
