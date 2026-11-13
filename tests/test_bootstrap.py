import pytest
from django.test import Client


@pytest.mark.django_db
def test_health():
    assert Client().get("/health/").status_code == 200
