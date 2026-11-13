from django.test import Client


def test_health():
    assert Client().get("/health/").status_code == 200
