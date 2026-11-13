from django.conf import settings


def installation(request):
    return {"fiscal_environment": settings.FISCAL_ENVIRONMENT, "app_version": "0.1.0"}
