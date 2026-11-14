from apps.core.models import CompanySettings
from apps.support.versioning import application_version


def installation(request):
    company = CompanySettings.objects.filter(pk=1).first()
    return {
        "fiscal_environment": company.fiscal_mode if company else "TEST",
        "app_version": application_version(),
        "company_settings": company,
        "has_company_logo": bool(getattr(company, "logo_data", None)),
    }
