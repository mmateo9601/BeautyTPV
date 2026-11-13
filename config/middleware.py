from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from apps.core.models import CompanySettings


class CompanyTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info == "/health/":
            return self.get_response(request)
        name = CompanySettings.objects.filter(pk=1).values_list("timezone", flat=True).first()
        try:
            zone = ZoneInfo(name or "Europe/Madrid")
        except (ValueError, ZoneInfoNotFoundError):
            zone = ZoneInfo("Europe/Madrid")
        with timezone.override(zone):
            return self.get_response(request)
