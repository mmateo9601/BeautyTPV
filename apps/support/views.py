import hashlib
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.accounts.permissions import ROLE_RANK, role_required
from apps.accounts.services import create_user, update_user
from apps.audit.services import record
from apps.hardware.models import Printer, PrintJob
from apps.verifactu.models import FiscalOutbox

from .forms import PrinterForm, TechnicalSettingsForm, UserCreateForm, UserUpdateForm
from .models import BackupRun, SupportSession, TechnicalSettings, UpdateRun
from .operations import backup_directory, backup_key, create_backup
from .services import (
    active_authorization,
    aeat_connectivity,
    authorize_support,
    diagnostics,
    require_authorization,
)


@role_required("SUPERADMIN", elevated=True)
def index(request):
    record(request.user, "support.view")
    return render(
        request,
        "support/index.html",
        {
            "diagnostics": diagnostics(),
            "printers": Printer.objects.all(),
            "print_jobs": PrintJob.objects.select_related("printer").order_by("-pk")[:30],
            "fiscal_outbox": FiscalOutbox.objects.select_related("record__invoice").order_by("-pk")[
                :30
            ],
            "backups": BackupRun.objects.order_by("-pk")[:20],
            "support_session": active_authorization(request.user),
            "support_sessions": SupportSession.objects.filter(actor=request.user).order_by("-pk")[
                :10
            ],
            "updates": UpdateRun.objects.order_by("-pk")[:10],
            "form": PrinterForm(),
        },
    )


@require_POST
@role_required("SUPERADMIN", elevated=True)
def authorize(request):
    try:
        authorize_support(
            request.user,
            request.POST.get("approver_username", ""),
            request.POST.get("password", ""),
            request.POST.get("justification", ""),
            request.POST.get("scope", "TECHNICAL"),
            request.META.get("REMOTE_ADDR", "unknown"),
        )
        messages.success(request, "Sesión de soporte autorizada durante 20 minutos.")
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    return redirect("support:index")


@require_POST
@role_required("SUPERADMIN", elevated=True)
def revoke(request, pk):
    session = get_object_or_404(SupportSession, pk=pk, actor=request.user)
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])
    record(request.user, "support.revoked", obj=session)
    return redirect("support:index")


@require_POST
@role_required("SUPERADMIN", elevated=True)
def diagnostic(request):
    require_authorization(request.user)
    result = diagnostics()
    if request.POST.get("network") == "1":
        result["aeat_connectivity"] = aeat_connectivity()
    record(request.user, "support.diagnostic")
    return JsonResponse(result)


@role_required("SUPERADMIN", elevated=True)
def export_diagnostics(request):
    require_authorization(request.user)
    result = diagnostics()
    record(request.user, "support.diagnostic_export")
    response = JsonResponse(result)
    response["Content-Disposition"] = 'attachment; filename="beautytpv-diagnostics.json"'
    return response


@require_POST
@role_required("SUPERADMIN", elevated=True)
def backup(request):
    require_authorization(request.user, "BACKUP")
    try:
        destination = backup_directory() / (
            "beautytpv-" + timezone.now().strftime("%Y%m%d%H%M%S%f") + ".btpv"
        )
        manifest, digest = create_backup(
            connection.settings_dict["NAME"], destination, backup_key()
        )
        run = BackupRun.objects.create(
            filename=destination.name, sha256=digest, created_by=request.user
        )
        record(request.user, "backup.created", obj=run)
        messages.success(request, "Copia cifrada creada y verificada.")
    except (ValueError, OSError) as error:
        messages.error(
            request,
            "Copia no creada: revise clave externa, ruta y permisos. " + type(error).__name__,
        )
    return redirect("support:index")


@role_required("SUPERADMIN", elevated=True)
def backup_download(request, pk):
    require_authorization(request.user, "BACKUP")
    run = get_object_or_404(BackupRun, pk=pk)
    path = backup_directory() / Path(run.filename).name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != run.sha256:
        return HttpResponse("Copia no disponible o hash incorrecto.", status=409)
    record(request.user, "backup.download", obj=run)
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


@role_required("SUPERADMIN", elevated=True)
def printer_save(request, pk=None):
    require_authorization(request.user)
    instance = get_object_or_404(Printer, pk=pk) if pk else None
    form = PrinterForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        printer = form.save()
        record(request.user, "device.saved", obj=printer)
        return redirect("support:index")
    return render(request, "support/settings.html", {"form": form, "title": "Dispositivo ESC/POS"})


@require_POST
@role_required("SUPERADMIN", elevated=True)
def recover_fiscal(request, pk):
    require_authorization(request.user)
    item = get_object_or_404(FiscalOutbox, pk=pk)
    if item.status not in ["RETRY", "PENDING"]:
        return HttpResponse(
            "Solo registros pendientes o reintentables. Rechazos requieren subsanación; aceptados no se reenvían.",
            status=409,
        )
    FiscalOutbox.objects.filter(pk=item.pk, status__in=["RETRY", "PENDING"]).update(
        next_attempt_at=timezone.now(), status="PENDING"
    )
    record(request.user, "fiscal.retry_requested", obj=item)
    return redirect("support:index")


@require_POST
@role_required("SUPERADMIN", elevated=True)
def correct_fiscal(request, pk):
    from apps.verifactu.services import correct_rejected

    require_authorization(request.user)
    item = get_object_or_404(FiscalOutbox.objects.select_related("record"), pk=pk)
    try:
        correct_rejected(item.record, request.user)
        messages.success(request, "Subsanación en cola; el registro original se conserva.")
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    return redirect("support:index")


@role_required("SUPERADMIN", elevated=True)
def technical_settings(request):
    require_authorization(request.user)
    form = TechnicalSettingsForm(request.POST or None, instance=TechnicalSettings.load())
    if request.method == "POST" and form.is_valid():
        form.save()
        record(request.user, "support.settings")
        return redirect("support:index")
    return render(request, "support/settings.html", {"form": form, "title": "Política de copias"})


@role_required("SUPERADMIN", elevated=True)
def updates(request):
    return render(
        request,
        "support/updates.html",
        {
            "updates": UpdateRun.objects.order_by("-pk")[:50],
            "instruction": "Detenga servicio y workers. Use scripts/update.ps1 con paquete local y SHA-256 obtenido de canal verificado. Copia previa y migraciones obligatorias. No ejecutar shell desde web.",
        },
    )


@role_required("ADMIN", elevated=True)
def users(request):
    form = UserCreateForm(request.POST or None)
    if request.user.role != "SUPERADMIN":
        form.fields["role"].choices = [
            (role, label)
            for role, label in User.Role.choices
            if ROLE_RANK[role] < ROLE_RANK[request.user.role]
        ]
    if request.method == "POST" and form.is_valid():
        try:
            create_user(
                request.user,
                **{
                    k: (v or None) if k in ["pin", "password"] else v
                    for k, v in form.cleaned_data.items()
                },
            )
            messages.success(request, "Usuario creado.")
            return redirect("team:index")
        except ValidationError as error:
            form.add_error(None, error)
    query = User.objects.order_by("username")
    if request.user.role != "SUPERADMIN":
        query = query.filter(
            role__in=[r for r in User.Role.values if ROLE_RANK[r] < ROLE_RANK[request.user.role]]
        )
    record(request.user, "user.list")
    return render(request, "support/users.html", {"users": query, "form": form})


@role_required("ADMIN", elevated=True)
def user_edit(request, pk):
    from apps.accounts.services import authorize_user_change

    target = get_object_or_404(User, pk=pk)
    authorize_user_change(request.user, target)
    form = UserUpdateForm(
        request.POST or None, initial={"role": target.role, "active": target.is_active}
    )
    if request.user.role != "SUPERADMIN":
        form.fields["role"].choices = [
            (role, label)
            for role, label in User.Role.choices
            if ROLE_RANK[role] < ROLE_RANK[request.user.role]
        ]
    if request.method == "POST" and form.is_valid():
        try:
            data = form.cleaned_data
            update_user(
                request.user,
                target,
                role=data["role"],
                active=data["active"],
                pin=data["pin"] or None,
                password=data["password"] or None,
            )
            messages.success(request, "Usuario actualizado; cambio auditado.")
            return redirect("team:index")
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, "support/user_edit.html", {"target": target, "form": form})


@role_required("SUPERADMIN", elevated=True)
def logs(request):
    require_authorization(request.user)
    from apps.audit.models import AuditEvent

    # Only technical event labels/status, never raw payloads or server exception text.
    events = list(
        AuditEvent.objects.filter(action__startswith="hardware.").values(
            "id", "action", "outcome", "created_at"
        )[:100]
    )
    events += list(
        AuditEvent.objects.filter(action__startswith="backup.").values(
            "id", "action", "outcome", "created_at"
        )[:100]
    )
    record(request.user, "support.logs")
    return JsonResponse({"events": events})
