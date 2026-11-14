from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.core.http import form_pk

from . import services
from .forms import SectionForm, StationForm
from .models import Section, Station


@role_required("ADMIN")
def index(request):
    stations = Station.objects.select_related("section").filter(
        name__icontains=request.GET.get("q", "")
    )
    if request.GET.get("section"):
        try:
            stations = stations.filter(section_id=form_pk(request.GET["section"]))
        except ValidationError as error:
            return HttpResponse("; ".join(error.messages), status=400)
    if request.GET.get("active") in ("yes", "no"):
        stations = stations.filter(active=request.GET["active"] == "yes")
    return render(
        request,
        "layout/index.html",
        {
            "sections": Section.objects.all(),
            "stations": stations,
            "section_form": SectionForm(),
            "station_form": StationForm(),
        },
    )


@require_POST
@role_required("ADMIN")
def section_create(request):
    form = SectionForm(request.POST)
    if form.is_valid():
        services.save_section(request.user, form.save(commit=False))
        messages.success(request, "Sección guardada.")
        return redirect("layout:index")
    return HttpResponse(form.errors.as_text(), status=400)


@role_required("ADMIN")
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    form = SectionForm(request.POST or None, instance=section)
    if request.method == "POST" and form.is_valid():
        services.save_section(request.user, form.save(commit=False))
        messages.success(request, "Sección guardada.")
        return redirect("layout:index")
    return render(request, "layout/form.html", {"form": form, "section": section})


@require_POST
@role_required("ADMIN")
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    try:
        services.delete_section(request.user, section)
        messages.success(request, "Sección eliminada.")
    except ProtectedError:
        return HttpResponse("Seccion con puestos: reasignelos antes de eliminarla.", status=400)
    return redirect("layout:index")


@role_required("ADMIN")
def station_edit(request, pk=None):
    station = get_object_or_404(Station, pk=pk) if pk else None
    form = StationForm(request.POST or None, instance=station)
    if request.method == "POST" and form.is_valid():
        try:
            services.save_station(request.user, form.save(commit=False))
            messages.success(request, "Puesto guardado.")
        except ValidationError as error:
            form.add_error(None, error)
            return render(
                request, "layout/form.html", {"form": form, "station": station}, status=400
            )
        return redirect("layout:index")
    return render(request, "layout/form.html", {"form": form, "station": station})


@require_POST
@role_required("ADMIN")
def station_delete(request, pk):
    station = get_object_or_404(Station, pk=pk)
    try:
        services.delete_station(request.user, station)
        messages.success(request, "Puesto eliminado.")
    except (ValidationError, ProtectedError):
        return HttpResponse("Puesto con historial protegido.", status=400)
    return redirect("layout:index")
