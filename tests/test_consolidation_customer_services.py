from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import update_user
from apps.audit.models import AuditEvent
from apps.customers.models import Customer
from apps.customers.services import delete_customer, save_customer
from apps.pos.models import OpenTicket
from apps.support.models import SupportSession

pytestmark = pytest.mark.django_db


def test_customer_service_mutations_require_role_and_support_pii():
    operator = User.objects.create_user(username="service-operator")
    admin = User.objects.create_user(username="service-admin", role="ADMIN")
    root = User.objects.create_user(username="service-root", role="SUPERADMIN")
    customer = save_customer(operator, Customer(name="Ficha de prueba"))
    assert AuditEvent.objects.filter(action="customer.save").exists()
    with pytest.raises(PermissionDenied):
        delete_customer(operator, customer)
    with pytest.raises(PermissionDenied):
        save_customer(root, Customer(name="Sin aprobacion PII"))
    SupportSession.objects.create(
        actor=root,
        approved_by=admin,
        scope="PII",
        justification="Revision autorizada",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    another = save_customer(root, Customer(name="Con aprobacion"))
    delete_customer(root, another)
    OpenTicket.objects.create(created_by=operator, customer=customer)
    with pytest.raises(ProtectedError):
        delete_customer(admin, customer)
    assert Customer.objects.filter(pk=customer.pk).exists()
    User.objects.filter(pk=operator.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        save_customer(operator, Customer(name="Actor obsoleto"))


def test_edit_staff_name_preserves_credentials_and_requires_current_hierarchy():
    actor = User.objects.create_user(username="name-admin", role="ADMIN")
    target = User.objects.create_user(username="name-worker", password="Worker password 849!")
    credentials = (target.password, target.pin_hash, target.auth_version)
    updated = update_user(actor, target, first_name=" Nombre editado ")
    assert updated.first_name == "Nombre editado"
    assert (updated.password, updated.pin_hash, updated.auth_version) == credentials
    User.objects.filter(pk=target.pk).update(role="SUPERADMIN")
    with pytest.raises(PermissionDenied):
        update_user(actor, target, first_name="Prohibido")
