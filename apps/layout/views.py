from django.core.exceptions import ValidationError
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
