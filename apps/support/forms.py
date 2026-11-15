import codecs

from django import forms

from apps.accounts.models import User
from apps.hardware.models import Printer

from .models import TechnicalSettings


class PrinterForm(forms.ModelForm):
    def clean(self):
        values = super().clean()
        kind = values.get("connection_type")
        if kind in ("TCP", "SERIAL") and not values.get("address", "").strip():
            self.add_error("address", "Indique dirección del dispositivo.")
        port = values.get("port", 0)
        if kind == "TCP" and not 1 <= port <= 65535:
            self.add_error("port", "Puerto TCP entre 1 y 65535.")
        if kind == "SERIAL" and port not in (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200):
            self.add_error("port", "Velocidad serie no admitida.")
        if kind == "USB" and not 1 <= values.get("usb_endpoint", 0) <= 255:
            self.add_error("usb_endpoint", "Endpoint USB entre 1 y 255.")
        if kind == "USB" and not all(
            1 <= values.get(field, 0) <= 65535 for field in ("usb_vendor", "usb_product")
        ):
            self.add_error(None, "Identificadores USB entre 1 y 65535.")
        try:
            codecs.lookup(values.get("encoding", ""))
        except LookupError:
            self.add_error("encoding", "Codificación desconocida.")
        if not 0 <= values.get("codepage", 0) <= 255:
            self.add_error("codepage", "Tabla ESC/POS entre 0 y 255.")
        from apps.hardware.drivers import simulator_allowed

        if kind == "SIMULATOR" and not simulator_allowed():
            self.add_error("connection_type", "Simulador deshabilitado fuera de desarrollo.")
        return values

    class Meta:
        model = Printer
        fields = [
            "name",
            "connection_type",
            "terminal",
            "address",
            "port",
            "usb_vendor",
            "usb_product",
            "usb_endpoint",
            "encoding",
            "codepage",
            "enabled",
            "cut_paper",
            "drawer_enabled",
        ]


class TechnicalSettingsForm(forms.ModelForm):
    class Meta:
        model = TechnicalSettings
        fields = ["backup_retention_days", "backup_interval_hours", "maintenance"]


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150, label="Usuario")
    first_name = forms.CharField(required=False, label="Nombre")
    role = forms.ChoiceField(choices=User.Role.choices, label="Rol")
    pin = forms.CharField(
        required=False, strip=False, widget=forms.PasswordInput, label="PIN de 6 a 12 dígitos"
    )
    password = forms.CharField(
        required=False, strip=False, widget=forms.PasswordInput, label="Contraseña administrativa"
    )


class UserUpdateForm(forms.Form):
    first_name = forms.CharField(required=False, max_length=150, label="Nombre")
    role = forms.ChoiceField(choices=User.Role.choices, label="Rol")
    active = forms.BooleanField(required=False, label="Activo")
    pin = forms.CharField(
        required=False, strip=False, widget=forms.PasswordInput, label="Nuevo PIN (vacío conserva)"
    )
    password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput,
        label="Nueva contraseña (vacío conserva)",
    )


class FiscalConfigurationForm(forms.ModelForm):
    class Meta:
        model = TechnicalSettings
        fields = ["certificate_path", "private_key_path", "fiscal_environment"]
        labels = {
            "certificate_path": "Referencia al certificado PEM externo",
            "private_key_path": "Referencia a clave PEM externa",
            "fiscal_environment": "Entorno de remisión",
        }

    def clean(self):
        values = super().clean()
        from .fiscal import validate_certificate_references

        validate_certificate_references(
            values.get("certificate_path", ""), values.get("private_key_path", "")
        )
        return values


class TerminalForm(forms.ModelForm):
    bridge_token = forms.CharField(
        required=False,
        min_length=32,
        max_length=256,
        widget=forms.PasswordInput,
        label="Nuevo token del bridge (vacío conserva)",
    )

    class Meta:
        from apps.core.models import Terminal

        model = Terminal
        fields = ["code", "name", "active", "default_section", "default_register"]

    def save(self, commit=True):
        terminal = super().save(commit=False)
        if self.cleaned_data.get("bridge_token"):
            terminal.set_bridge_token(self.cleaned_data["bridge_token"])
        if commit:
            terminal.save()
        return terminal


class PackageCheckForm(forms.Form):
    package_path = forms.CharField(label="Ruta del paquete ZIP local")
    sha256 = forms.RegexField(r"^[a-fA-F0-9]{64}$", label="SHA-256 del canal verificado")


class RestorePlanForm(forms.Form):
    backup = forms.ModelChoiceField(queryset=None, label="Copia cifrada a verificar")
    confirmation = forms.CharField(label="Escriba PREPARAR RESTAURACION")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import BackupRun

        self.fields["backup"].queryset = BackupRun.objects.filter(status="COMPLETE").order_by("-pk")

    def clean_confirmation(self):
        if self.cleaned_data["confirmation"] != "PREPARAR RESTAURACION":
            raise forms.ValidationError("Confirmacion incorrecta.")
        return self.cleaned_data["confirmation"]


class IncidentForm(forms.Form):
    from .models import Incident

    title = forms.CharField(max_length=160, label="Titulo")
    description = forms.CharField(
        max_length=1000, widget=forms.Textarea, label="Descripcion sin datos personales"
    )
    category = forms.ChoiceField(choices=Incident.Category.choices, label="Categoria")
    severity = forms.ChoiceField(
        choices=Incident.Severity.choices, label="Severidad", initial="MEDIUM"
    )

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        if actor.role != "SUPERADMIN":
            self.fields["category"].choices = [("OPERATIONAL", "Operativa")]

    def clean_title(self):
        from .incidents import incident_text

        return incident_text(self.cleaned_data["title"], 160)

    def clean_description(self):
        from .incidents import incident_text

        return incident_text(self.cleaned_data["description"], 1000)


class IncidentActionForm(forms.Form):
    from .models import Incident

    note = forms.CharField(
        max_length=1000, widget=forms.Textarea, label="Actuacion o motivo sin datos personales"
    )
    status = forms.ChoiceField(choices=Incident.Status.choices, label="Estado")
    category = forms.ChoiceField(choices=Incident.Category.choices, label="Categoria")
    severity = forms.ChoiceField(choices=Incident.Severity.choices, label="Severidad")
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        if actor.role != "SUPERADMIN":
            self.fields["category"].choices = [("OPERATIONAL", "Operativa")]

    def clean_note(self):
        from .incidents import incident_text

        return incident_text(self.cleaned_data["note"], 1000)
