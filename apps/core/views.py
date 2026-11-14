from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required

from .forms import (
    CommercialSettingsForm,
    CompanySettingsForm,
    FiscalSettingsForm,
    LogoForm,
    PosSettingsForm,
)
from .models import CompanySettings
from .services import save_company_settings

SETTINGS_SECTIONS = [("commercial", "Salón"), ("fiscal", "Fiscal"), ("pos", "TPV")]
FORMS = {
    "legacy": CompanySettingsForm,
    "commercial": CommercialSettingsForm,
    "fiscal": FiscalSettingsForm,
    "pos": PosSettingsForm,
}


def _context(company, form, section, logo_form=None):
    return {
        "form": form,
        "company": company,
        "settings_section": section,
        "settings_sections": SETTINGS_SECTIONS,
        "logo_form": logo_form or LogoForm(),
    }


@role_required("ADMIN", elevated=True)
def settings(request):
    company = CompanySettings.load()
    section = request.GET.get("section", "legacy" if request.method == "POST" else "commercial")
    if section not in FORMS:
        return HttpResponse("Sección de ajustes no válida.", status=400)
    form = FORMS[section](request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid():
        try:
            company = save_company_settings(request.user, form.cleaned_data)
            messages.success(
                request,
                "Ajustes guardados. Los documentos emitidos conservan sus datos originales.",
            )
            return redirect(request.path + ("?section=" + section if section != "legacy" else ""))
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request,
        "core/settings.html",
        _context(company, form, section),
        status=400 if request.method == "POST" else 200,
    )


@role_required("EMPLOYEE")
def logo(request):
    image = CompanySettings.load().logo_data
    if not image:
        return HttpResponse(status=404)
    response = HttpResponse(bytes(image), content_type="image/png")
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@require_POST
@role_required("ADMIN", elevated=True)
def logo_save(request):
    form = LogoForm(request.POST, request.FILES)
    company = CompanySettings.load()
    if form.is_valid():
        try:
            save_company_settings(
                request.user,
                {},
                logo=form.cleaned_data.get("logo"),
                remove_logo=form.cleaned_data["remove_logo"],
            )
            messages.success(request, "Logotipo actualizado.")
            return redirect("/empresa/?section=commercial")
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request,
        "core/settings.html",
        _context(company, CommercialSettingsForm(instance=company), "commercial", form),
        status=400,
    )
