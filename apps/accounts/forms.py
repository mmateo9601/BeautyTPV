from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=150)
    credential = forms.CharField(label="PIN o contraseña", widget=forms.PasswordInput)
    password_mode = forms.BooleanField(label="Acceder con contraseña", required=False)


class ElevateForm(forms.Form):
    password = forms.CharField(label="Confirme su contraseña", widget=forms.PasswordInput)
