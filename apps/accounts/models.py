import json
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import salted_hmac


class InternalUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields["role"] = "SUPERADMIN"
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Empleado"
        MANAGER = "MANAGER", "Encargado"
        ADMIN = "ADMIN", "Administrador"
        SUPERADMIN = "SUPERADMIN", "Superadmin"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.EMPLOYEE)
    pin_hash = models.CharField(max_length=128, blank=True, editable=False)
    auth_version = models.PositiveIntegerField(default=0, editable=False)
    objects = InternalUserManager()

    def _get_session_auth_hash(self, secret=None):
        # Django also calls this method for SECRET_KEY_FALLBACKS. Credential and
        # role changes must invalidate a PIN session as well as password sessions.
        state = json.dumps(
            [self.password, self.pin_hash, self.role, self.is_active, self.auth_version]
        )
        return salted_hmac(
            "beautytpv.accounts.User.session_security_state",
            state,
            secret=secret,
            algorithm="sha256",
        ).hexdigest()

    def set_pin(self, pin):
        if (
            not isinstance(pin, str)
            or not pin.isascii()
            or not pin.isdigit()
            or not 6 <= len(pin) <= 12
        ):
            raise ValidationError("El PIN debe contener entre 6 y 12 dígitos.")
        self.pin_hash = make_password(pin)

    def check_pin(self, pin):
        return bool(self.pin_hash) and check_password(pin, self.pin_hash)


class LoginThrottle(models.Model):
    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def locked(self):
        return self.locked_until is not None and self.locked_until > timezone.now()

    def fail(self):
        self.failures += 1
        if self.failures >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=15)
        self.save()
