from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.core.http import form_pk

from . import services
from .models import CashMovement, CashRegister, CashSession


@role_required("EMPLOYEE")
def index(request):
    sessions = CashSession.objects.select_related("register").order_by("-opened_at")
    if request.user.role == "EMPLOYEE":
        sessions = sessions.filter(Q(closed_at__isnull=True) | Q(opened_by=request.user))
    return render(
        request,
        "cash/index.html",
        {
            "registers": CashRegister.objects.all(),
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
