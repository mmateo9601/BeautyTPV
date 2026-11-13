from django.shortcuts import redirect, render

from apps.accounts.permissions import role_required
from apps.audit.services import record

from .forms import CompanySettingsForm
from .models import CompanySettings


@role_required("ADMIN", elevated=True)
def settings(request):
    company = CompanySettings.load()
    form = CompanySettingsForm(request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid():
        form.save()
        record(request.user, "company.settings", obj=company)
        return redirect("core:settings")
    return render(request, "core/settings.html", {"form": form, "company": company})
