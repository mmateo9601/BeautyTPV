from django.core.paginator import Paginator
from django.shortcuts import render

from apps.accounts.permissions import role_required

from .models import AuditEvent


@role_required("ADMIN", elevated=True)
def index(request):
    events = AuditEvent.objects.select_related("actor").all()
    action = request.GET.get("action", "")[:100]
    if action:
        events = events.filter(action=action)
    page = Paginator(events, 100).get_page(request.GET.get("page"))
    return render(request, "audit/index.html", {"events": page, "page_obj": page, "action": action})
