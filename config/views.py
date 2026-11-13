from datetime import timedelta

from django.db import connection
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.support.models import ServiceHeartbeat
from apps.support.versioning import application_version


@require_GET
def health(request):
    """Public liveness with measured DB/supervisor state; no paths, PIDs or PII."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        service = ServiceHeartbeat.objects.filter(name="service").first()
        supervised = service is not None
        healthy = not supervised or (
            service.state == "RUNNING"
            and service.last_seen >= timezone.now() - timedelta(seconds=30)
        )
        return JsonResponse(
            {
                "web": "OK",
                "database": "OK",
                "supervised": supervised,
                "workers": "SUPERVISED"
                if healthy and supervised
                else ("UNSUPERVISED" if not supervised else "UNHEALTHY"),
                "version": application_version(),
            },
            status=200 if healthy else 503,
        )
    except DatabaseError:
        return JsonResponse({"web": "OK", "database": "UNAVAILABLE"}, status=503)
