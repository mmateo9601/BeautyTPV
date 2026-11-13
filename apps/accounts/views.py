from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit.services import record

from .forms import ElevateForm, LoginForm
from .services import authenticate_local, elevation_expiry


@require_http_methods(["GET", "POST"])
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate_local(form.cleaned_data["username"], form.cleaned_data["credential"], request.META.get("REMOTE_ADDR", "unknown"), password=form.cleaned_data["password_mode"], request=request)
        if user:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            if form.cleaned_data["password_mode"]:
                request.session["elevated_until"] = elevation_expiry()
            return redirect("/tpv/")
        form.add_error(None, "Acceso no válido o temporalmente bloqueado.")
    return render(request, "accounts/login.html", {"form": form})


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
        user = authenticate_local(request.user.username, form.cleaned_data["password"], request.META.get("REMOTE_ADDR", "unknown"), password=True, request=request)
        if user:
            request.session.cycle_key()
            request.session["elevated_until"] = elevation_expiry()
            record(user, "auth.elevated")
            return redirect("/soporte/" if user.role == "SUPERADMIN" else "/tpv/")
        form.add_error(None, "Contraseña incorrecta o acceso bloqueado.")
    return render(request, "accounts/elevate.html", {"form": form})
