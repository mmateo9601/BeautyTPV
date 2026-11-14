"""Customer mutations shared by HTTP and non-HTTP callers."""

from django.db import transaction

from apps.accounts.permissions import require_role
from apps.audit.services import record


def require_customer_access(actor):
    require_role(actor, "EMPLOYEE")
    if actor.role == "SUPERADMIN":
        from apps.support.services import require_authorization

        require_authorization(actor, "PII")


@transaction.atomic
def save_customer(actor, customer):
    require_customer_access(actor)
    customer.full_clean()
    customer.save()
    record(actor, "customer.save", obj=customer)
    return customer


@transaction.atomic
def delete_customer(actor, customer):
    require_role(actor, "ADMIN")
    require_customer_access(actor)
    pk = customer.pk
    customer.delete()
    record(actor, "customer.deleted", target=str(pk))
