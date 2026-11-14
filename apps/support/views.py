import hashlib
import zipfile
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.accounts.permissions import ROLE_RANK, require_elevated, role_required
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

FISCAL_STATUSES = [
    (value, value)
    for value in (
        "PENDING",
        "SENDING",
        "ACCEPTED",
        "ACCEPTED_WITH_ERRORS",
        "REJECTED",
        "RETRY",
        "DUPLICATE_REVIEW",
    )
]


@role_required("SUPERADMIN", elevated=True)
def index(request):
    record(request.user, "support.view")
    printers = Printer.objects.all()
    if request.GET.get("q"):
        printers = printers.filter(name__icontains=request.GET["q"])
    print_jobs = PrintJob.objects.select_related("printer").order_by("-pk")
    fiscal_outbox = FiscalOutbox.objects.select_related("record__invoice").order_by("-pk")
    if request.GET.get("print_status") in PrintJob.Status.values:
        print_jobs = print_jobs.filter(status=request.GET["print_status"])
    if request.GET.get("fiscal_status") in [value for value, _ in FISCAL_STATUSES]:
        fiscal_outbox = fiscal_outbox.filter(status=request.GET["fiscal_status"])
    return render(
        request,
        "support/index.html",
        {
            "diagnostics": diagnostics(),
            "printers": printers,
            "print_jobs": print_jobs[:30],
            "fiscal_outbox": fiscal_outbox[:30],
            "print_statuses": PrintJob.Status.choices,
            "fiscal_statuses": FISCAL_STATUSES,
            "filters": request.GET,
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
        record(request.user, "backup.failed", outcome="FAILED")
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
        from apps.hardware.services import save_printer

        try:
            save_printer(form.save(commit=False), request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(
                request, "Dispositivo guardado; los trabajos anteriores conservan su intencion."
            )
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


@require_POST
@role_required("SUPERADMIN", elevated=True)
def annul_fiscal(request, pk):
    from apps.verifactu.services import annul_record

    require_authorization(request.user)
    if request.POST.get("confirmation") != "ANULAR REGISTRO":
        return HttpResponse(
            "Confirme ANULAR REGISTRO. Una devolucion requiere rectificativa.", status=400
        )
    item = get_object_or_404(FiscalOutbox.objects.select_related("record"), pk=pk)
    if item.record.record_type != "ALTA":
        return HttpResponse("Seleccione el registro de alta original.", status=400)
    try:
        annul_record(
            item.record,
            request.user,
            request.POST.get("reason", ""),
            without_previous=request.POST.get("without_previous") == "1",
        )
        messages.success(
            request, "Anulacion registral en cola. No modifica ni devuelve la venta original."
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    return redirect("support:index")


@role_required("SUPERADMIN", elevated=True)
def technical_settings(request):
    require_authorization(request.user)
    form = TechnicalSettingsForm(request.POST or None, instance=TechnicalSettings.load())
    if request.method == "POST" and form.is_valid():
        from .services import save_technical_settings

        save_technical_settings(request.user, form.save(commit=False))
        messages.success(request, "Politica de mantenimiento guardada.")
        return redirect("support:index")
    return render(request, "support/settings.html", {"form": form, "title": "Política de copias"})


@role_required("SUPERADMIN", elevated=True)
def updates(request):
    from .forms import PackageCheckForm
    from .updates import validate_package
    from .versioning import application_version

    candidate_form = PackageCheckForm(request.POST or None)
    candidate = None
    if request.method == "POST":
        require_authorization(request.user, "UPDATE")
        if candidate_form.is_valid():
            try:
                candidate = validate_package(
                    candidate_form.cleaned_data["package_path"],
                    candidate_form.cleaned_data["sha256"],
                )
                candidate = {"version": candidate["version"], "files": len(candidate["files"])}
                record(
                    request.user,
                    "update.package_checked",
                    metadata={"sha256": candidate_form.cleaned_data["sha256"]},
                )
            except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
                candidate_form.add_error(
                    None, "Paquete no válido o no accesible: " + type(error).__name__
                )
    return render(
        request,
        "support/updates.html",
        {
            "updates": UpdateRun.objects.order_by("-pk")[:50],
            "current_version": application_version(),
            "candidate_form": candidate_form,
            "candidate": candidate,
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
    if request.GET.get("q"):
        query = query.filter(
            Q(username__icontains=request.GET["q"]) | Q(first_name__icontains=request.GET["q"])
        )
    if request.GET.get("state") in ("active", "inactive"):
        query = query.filter(is_active=request.GET["state"] == "active")
    if request.GET.get("role") in User.Role.values:
        query = query.filter(role=request.GET["role"])
    record(request.user, "user.list")
    return render(
        request,
        "support/users.html",
        {"users": query, "form": form, "filters": request.GET, "roles": User.Role.choices},
    )


@role_required("ADMIN", elevated=True)
def user_edit(request, pk):
    from apps.accounts.services import authorize_user_change

    target = get_object_or_404(User, pk=pk)
    authorize_user_change(request.user, target)
    form = UserUpdateForm(
        request.POST or None,
        initial={"role": target.role, "active": target.is_active, "first_name": target.first_name},
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
                first_name=data["first_name"],
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


@require_POST
@role_required("ADMIN", elevated=True)
def unlock_user(request, pk):
    from apps.accounts.models import LoginThrottle
    from apps.accounts.services import _throttle_keys, authorize_user_change

    target = get_object_or_404(User, pk=pk)
    authorize_user_change(request.user, target)
    keys = [_throttle_keys(target.username, "")[0]]
    origin = request.POST.get("origin", "").strip()
    if origin:
        require_authorization(request.user)
        keys.append(_throttle_keys(target.username, origin)[1])
    with transaction.atomic():
        count = LoginThrottle.objects.filter(key__in=keys).update(failures=0, locked_until=None)
        record(request.user, "user.pin_unlocked", obj=target, metadata={"count": count})
    messages.success(request, "Bloqueo de acceso retirado; el PIN se conserva.")
    return redirect("team:edit", pk=pk)


@role_required("SUPERADMIN", elevated=True)
def terminals(request):
    from apps.core.models import Terminal

    from .forms import TerminalForm

    require_authorization(request.user)
    form = TerminalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        terminal = form.save(commit=False)
        from .services import save_terminal

        try:
            save_terminal(request.user, terminal)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Terminal creada.")
            return redirect("support:terminals")
    query = Terminal.objects.order_by("code")
    if request.GET.get("q"):
        query = query.filter(
            Q(name__icontains=request.GET["q"]) | Q(code__icontains=request.GET["q"])
        )
    if request.GET.get("active") in ("1", "0"):
        query = query.filter(active=request.GET["active"] == "1")
    return render(
        request,
        "support/terminals.html",
        {"terminals": query, "form": form, "filters": request.GET},
    )


@role_required("SUPERADMIN", elevated=True)
def terminal_edit(request, pk):
    from apps.core.models import Terminal

    from .forms import TerminalForm

    require_authorization(request.user)
    terminal = get_object_or_404(Terminal, pk=pk)
    form = TerminalForm(request.POST or None, instance=terminal)
    if request.method == "POST" and form.is_valid():
        terminal = form.save(commit=False)
        from .services import save_terminal

        try:
            save_terminal(request.user, terminal)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Terminal actualizada.")
            return redirect("support:terminals")
    return render(
        request, "support/settings.html", {"form": form, "title": "Terminal y autorización bridge"}
    )


@role_required("SUPERADMIN", elevated=True)
def fiscal_settings(request):
    from .forms import FiscalConfigurationForm

    require_authorization(request.user)
    form = FiscalConfigurationForm(request.POST or None, instance=TechnicalSettings.load())
    if request.method == "POST" and form.is_valid():
        from django.db import transaction

        from apps.core.models import CompanySettings

        with transaction.atomic():
            configuration = form.save()
            company = CompanySettings.load()
            company.fiscal_mode = configuration.fiscal_environment
            company.save(update_fields=["fiscal_mode"])
        record(request.user, "fiscal.configuration", metadata={"status": "REFERENCES_CONFIGURED"})
        messages.success(
            request,
            "Referencias guardadas; producción permanece bloqueada hasta validación oficial.",
        )
        return redirect("support:index")
    return render(
        request,
        "support/settings.html",
        {"form": form, "title": "Certificado externo y entorno fiscal"},
    )


@role_required("SUPERADMIN", elevated=True)
def restore_advisor(request):
    """Prepare and audit a verified offline recovery, never swap a live DB over HTTP."""
    from django.db.models import Max

    from apps.billing.models import Invoice

    from .forms import RestorePlanForm
    from .operations import inspect_backup

    require_authorization(request.user, "BACKUP")
    form = RestorePlanForm(request.POST or None)
    plan = None
    if request.method == "POST" and form.is_valid():
        run = form.cleaned_data["backup"]
        archive = backup_directory() / Path(run.filename).name
        try:
            if hashlib.sha256(archive.read_bytes()).hexdigest() != run.sha256:
                raise ValueError("Hash incorrecto")
            manifest, _ = inspect_backup(archive, backup_key())
            current = Invoice.objects.aggregate(value=Max("pk"))["value"] or 0
            restored = manifest.get("fiscal_watermarks", {}).get("billing_invoice") or 0
            with transaction.atomic():
                policy = TechnicalSettings.load()
                policy.maintenance = True
                policy.save(update_fields=["maintenance"])
                record(
                    request.user,
                    "restore.prepared",
                    obj=run,
                    metadata={"sha256": run.sha256, "status": "MAINTENANCE"},
                )
            plan = {
                "filename": run.filename,
                "current_invoice_id": current,
                "backup_invoice_id": restored,
                "records_at_risk": max(0, current - restored),
                "database_sha256": manifest["database_sha256"],
            }
        except Exception:
            # Do not expose encryption material, certificate paths or database contents.
            record(request.user, "restore.preparation_failed", obj=run, outcome="FAILED")
            form.add_error(
                None, "No se pudo verificar la copia. Revise clave externa, integridad y permisos."
            )
    return render(request, "support/restore.html", {"form": form, "plan": plan})


@require_POST
@role_required("ADMIN", elevated=True)
def revoke_user_sessions(request, pk):
    from apps.accounts.services import revoke_user_sessions as revoke_sessions

    if request.POST.get("confirmation") != "REVOCAR SESIONES":
        return HttpResponse(
            "Confirme REVOCAR SESIONES para invalidar los accesos existentes.", status=400
        )
    target = get_object_or_404(User, pk=pk)
    revoke_sessions(request.user, target)
    messages.success(
        request, "Sesiones y autorizaciones revocadas. Las credenciales no han cambiado."
    )
    return redirect("team:index")


@role_required("MANAGER")
def incidents(request):
    if request.user.role == "SUPERADMIN":
        require_elevated(request)
    from .forms import IncidentForm
    from .incidents import create_incident, visible_incidents
    from .models import Incident

    query = visible_incidents(request.user)
    form = IncidentForm(request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            item = create_incident(request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Incidencia registrada.")
            return redirect("support:incident_detail", pk=item.pk)
    for field, choices in (
        ("status", Incident.Status),
        ("severity", Incident.Severity),
        ("category", Incident.Category),
    ):
        if request.GET.get(field) in choices.values:
            query = query.filter(**{field: request.GET[field]})
    if request.GET.get("q"):
        query = query.filter(title__icontains=request.GET["q"])
    record(request.user, "incident.list")
    return render(
        request,
        "support/incidents.html",
        {
            "incidents": query[:200],
            "form": form,
            "filters": request.GET,
            "statuses": Incident.Status.choices,
            "severities": Incident.Severity.choices,
            "categories": form.fields["category"].choices,
        },
    )


@role_required("MANAGER")
def incident_detail(request, pk):
    if request.user.role == "SUPERADMIN":
        require_elevated(request)
    from .forms import IncidentActionForm
    from .incidents import add_action, authorize_incident
    from .models import Incident

    item = get_object_or_404(Incident, pk=pk)
    authorize_incident(request.user, item.category)
    form = IncidentActionForm(
        request.POST or None,
        actor=request.user,
        initial={
            "status": item.status,
            "category": item.category,
            "severity": item.severity,
            "version": item.version,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            add_action(request.user, item, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Actuacion registrada y estado actualizado.")
            return redirect("support:incident_detail", pk=pk)
    record(request.user, "incident.view", obj=item)
    return render(
        request,
        "support/incident_detail.html",
        {"incident": item, "actions": item.actions.select_related("actor"), "form": form},
    )


@require_POST
@role_required("SUPERADMIN", elevated=True)
def backup_verify(request, pk):
    from .operations import inspect_backup

    require_authorization(request.user, "BACKUP")
    run = get_object_or_404(BackupRun, pk=pk, status="COMPLETE")
    path = backup_directory() / Path(run.filename).name
    try:
        if hashlib.sha256(path.read_bytes()).hexdigest() != run.sha256:
            raise ValueError("Hash incorrecto")
        inspect_backup(path, backup_key())
    except Exception:
        record(request.user, "backup.verification_failed", obj=run, outcome="FAILED")
        messages.error(request, "No se pudo verificar la copia: revise integridad y clave externa.")
        return redirect("support:index")
    record(request.user, "backup.verified", obj=run, metadata={"sha256": run.sha256})
    messages.success(
        request, "Copia cifrada verificada sin activar mantenimiento ni restaurar datos."
    )
    return redirect("support:index")
