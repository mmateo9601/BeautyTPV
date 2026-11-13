from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit.context import terminal_context
from apps.audit.services import record

from .forms import ElevateForm, LoginForm
from .models import User
from .services import authenticate_local, elevation_expiry


@require_http_methods(["GET", "POST"])
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        terminal = form.cleaned_data["terminal"]
        with terminal_context(terminal.pk if terminal else None):
            user = authenticate_local(
                form.cleaned_data["username"],
                form.cleaned_data["credential"],
                request.META.get("REMOTE_ADDR", "unknown"),
                password=form.cleaned_data["password_mode"],
                request=request,
            )
        if user:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            # Django preserves the session when the same user logs in again.
            # A new PIN authentication must never inherit password elevation.
            request.session.pop("elevated_until", None)
            request.session.pop("terminal_id", None)
            if terminal:
                request.session["terminal_id"] = terminal.pk
            if form.cleaned_data["password_mode"]:
                request.session["elevated_until"] = elevation_expiry()
            return redirect("/tpv/")
        form.add_error(None, "Acceso no válido o temporalmente bloqueado.")
    users = (
        User.objects.filter(is_active=True, role__in=["EMPLOYEE", "MANAGER"])
        .exclude(pin_hash="")
        .only("username")
    )
    return render(request, "accounts/login.html", {"form": form, "users": users})


@require_POST
def logout_view(request):
    record(request.user, "auth.logout")
    logout(request)
    return redirect("/acceso/")


@login_required
@require_http_methods(["GET", "POST"])
def elevate_view(request):
    form = ElevateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate_local(
            request.user.username,
            form.cleaned_data["password"],
            request.META.get("REMOTE_ADDR", "unknown"),
            password=True,
            request=request,
        )
        if user:
            # Password verification can upgrade the stored password hash.
            # Preserve only the newly verified security state in this session.
            update_session_auth_hash(request, user)
            request.session["elevated_until"] = elevation_expiry()
            record(user, "auth.elevated")
            return redirect("/soporte/" if user.role == "SUPERADMIN" else "/tpv/")
        form.add_error(None, "Contraseña incorrecta o acceso bloqueado.")
    return render(request, "accounts/elevate.html", {"form": form})
