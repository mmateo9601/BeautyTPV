from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    credential = forms.CharField(label="PIN o contraseña", widget=forms.PasswordInput, strip=False)
    password_mode = forms.BooleanField(label="Acceder con contraseña", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.core.models import Terminal

        self.fields["terminal"] = forms.ModelChoiceField(
            label="Terminal",
            queryset=Terminal.objects.filter(active=True).order_by("name"),
            required=False,
            empty_label="Sin terminal asignado",
        )


class ElevateForm(forms.Form):
    password = forms.CharField(
        label="Confirme su contraseña", widget=forms.PasswordInput, strip=False
    )
