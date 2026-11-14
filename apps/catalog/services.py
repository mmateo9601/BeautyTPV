from django.db import transaction

from apps.accounts.permissions import require_role
from apps.audit.services import record


@transaction.atomic
def save_catalog_item(actor, item):
    require_role(actor, "ADMIN")
    item.full_clean()
    item.save()
    record(actor, "catalog.save", obj=item)
    return item


@transaction.atomic
def save_category(actor, category):
    require_role(actor, "ADMIN")
    category.full_clean()
    category.save()
    record(actor, "catalog.category", obj=category)
    return category


@transaction.atomic
def delete_category(actor, category):
    require_role(actor, "ADMIN")
    pk = category.pk
    category.delete()
    record(actor, "catalog.category.deleted", target=str(pk))
