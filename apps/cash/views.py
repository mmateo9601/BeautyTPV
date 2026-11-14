from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.core.http import form_pk

from . import services
from .forms import CashRegisterForm
from .models import CashMovement, CashRegister, CashSession


@role_required("EMPLOYEE")
def index(request):
    sessions = CashSession.objects.select_related("register").order_by("-opened_at")
    if request.user.role == "EMPLOYEE":
        sessions = sessions.filter(Q(closed_at__isnull=True) | Q(opened_by=request.user))
    if request.GET.get("status") in ("open", "closed"):
        sessions = sessions.filter(closed_at__isnull=request.GET["status"] == "open")
    if request.GET.get("q"):
        sessions = sessions.filter(register__name__icontains=request.GET["q"])
    if request.GET.get("register"):
        try:
            sessions = sessions.filter(register_id=form_pk(request.GET["register"]))
        except ValidationError as error:
            return HttpResponse("; ".join(error.messages), status=400)
    return render(
        request,
        "cash/index.html",
        {
            "registers": CashRegister.objects.filter(active=True).filter(
                Q(terminal__isnull=True) | Q(terminal__active=True)
            ),
            "all_registers": CashRegister.objects.all(),
            "sessions": sessions[:100],
            "movements": CashMovement.objects.filter(session__in=sessions).order_by("-created_at")[
                :100
            ],
        },
    )


@require_POST
@role_required("EMPLOYEE")
def open(request):
    try:
        services.open_session(
            get_object_or_404(CashRegister, pk=form_pk(request.POST.get("register_id"))),
            request.user,
            request.POST.get("opening_balance", "0"),
        )
    except ValidationError as exc:
        return HttpResponse("; ".join(exc.messages), status=400)
    return redirect("cash:index")


@require_POST
@role_required("MANAGER")
def movement(request, pk):
    try:
        services.add_movement(
            get_object_or_404(CashSession, pk=pk),
            request.user,
            request.POST.get("kind"),
            request.POST.get("amount"),
            request.POST.get("reason", ""),
        )
    except ValidationError as exc:
        return HttpResponse("; ".join(exc.messages), status=400)
    return redirect("cash:index")


@require_POST
@role_required("MANAGER")
def close(request, pk):
    try:
        services.close_session(
            get_object_or_404(CashSession, pk=pk), request.user, request.POST.get("counted")
        )
    except ValidationError as exc:
        return HttpResponse("; ".join(exc.messages), status=400)
    return redirect("cash:index")


@role_required("ADMIN")
def registers(request):
    query = CashRegister.objects.select_related("terminal").all()
    if request.GET.get("q"):
        query = query.filter(name__icontains=request.GET["q"])
    if request.GET.get("active") in ("yes", "no"):
        query = query.filter(active=request.GET["active"] == "yes")
    if request.GET.get("terminal"):
        try:
            query = query.filter(terminal_id=form_pk(request.GET["terminal"]))
        except ValidationError as error:
            return HttpResponse("; ".join(error.messages), status=400)
    from apps.core.models import Terminal

    return render(
        request,
        "cash/registers.html",
        {
            "registers": query,
            "form": CashRegisterForm(),
            "terminals": Terminal.objects.all(),
            "selected": None,
        },
    )


@require_POST
@role_required("ADMIN")
def register_create(request):
    return register_edit(request)


@role_required("ADMIN")
def register_edit(request, pk=None):
    register = get_object_or_404(CashRegister, pk=pk) if pk else None
    form = CashRegisterForm(request.POST or None, instance=register)
    if request.method == "POST" and form.is_valid():
        try:
            services.save_register(request.user, form.save(commit=False))
            messages.success(
                request, "Caja guardada. Se conserva el historial de turnos y movimientos."
            )
            return redirect("cash:registers")
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request,
        "cash/register_form.html",
        {"form": form, "register": register, "title": "Editar caja" if register else "Nueva caja"},
        status=400 if request.method == "POST" else 200,
    )
