from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.audit.services import record

from .forms import SectionForm, StationForm
from .models import Section, Station


@role_required("ADMIN")
def index(request):
    return render(
        request,
        "layout/index.html",
        {
            "sections": Section.objects.all(),
            "stations": Station.objects.select_related("section"),
            "section_form": SectionForm(),
            "station_form": StationForm(),
        },
    )


@require_POST
@role_required("ADMIN")
def section_create(request):
    form = SectionForm(request.POST)
    if form.is_valid():
        obj = form.save()
        record(request.user, "layout.section", obj=obj)
        return redirect("layout:index")
    return HttpResponse(form.errors.as_text(), status=400)


@role_required("ADMIN")
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    form = SectionForm(request.POST or None, instance=section)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            section = form.save()
            record(request.user, "layout.section.updated", obj=section)
        return redirect("layout:index")
    return render(request, "layout/form.html", {"form": form, "section": section})


@require_POST
@role_required("ADMIN")
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    try:
        with transaction.atomic():
            section.delete()
            record(request.user, "layout.section.deleted", target=str(pk))
    except ProtectedError:
        return HttpResponse("Seccion con puestos: reasignelos antes de eliminarla.", status=400)
    return redirect("layout:index")


@role_required("ADMIN")
def station_edit(request, pk=None):
    station = get_object_or_404(Station, pk=pk) if pk else None
    form = StationForm(request.POST or None, instance=station)
    if request.method == "POST" and form.is_valid():
        if (
            station
            and not form.cleaned_data["active"]
            and station.tickets.filter(status__in=["OPEN", "PAYMENT_PENDING"]).exists()
        ):
            return HttpResponse("Puesto con cuenta abierta.", status=400)
        obj = form.save()
        record(request.user, "layout.station", obj=obj)
        return redirect("layout:index")
    return render(request, "layout/form.html", {"form": form, "station": station})


@require_POST
@role_required("ADMIN")
def station_delete(request, pk):
    station = get_object_or_404(Station, pk=pk)
    try:
        record(request.user, "layout.station.delete", obj=station)
        station.delete()
    except (ValidationError, ProtectedError):
        return HttpResponse("Puesto con historial protegido.", status=400)
    return redirect("layout:index")
