from apps.core.models import CompanySettings
from apps.support.versioning import application_version


def installation(request):
    mode = CompanySettings.objects.filter(pk=1).values_list("fiscal_mode", flat=True).first()
    return {"fiscal_environment": mode or "TEST", "app_version": application_version()}
