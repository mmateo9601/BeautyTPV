from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.permissions import require_role
from apps.audit.services import record

from .models import Station


@transaction.atomic
def save_section(actor, section):
    require_role(actor, "ADMIN")
    section.full_clean()
    section.save()
    record(actor, "layout.section", obj=section)
    return section


@transaction.atomic
def save_station(actor, station):
    require_role(actor, "ADMIN")
    if station.pk:
        current = Station.objects.get(pk=station.pk)
        if current.tickets.filter(status__in=["OPEN", "PAYMENT_PENDING"]).exists() and (
            not station.active or station.section_id != current.section_id
        ):
            raise ValidationError("No puede desactivar ni reasignar un puesto con cuenta abierta.")
    station.full_clean()
    station.save()
    record(actor, "layout.station", obj=station)
    return station


@transaction.atomic
def delete_station(actor, station):
    require_role(actor, "ADMIN")
    pk = station.pk
    station.delete()
    record(actor, "layout.station.delete", target=str(pk))


@transaction.atomic
def delete_section(actor, section):
    require_role(actor, "ADMIN")
    pk = section.pk
    section.delete()
    record(actor, "layout.section.deleted", target=str(pk))
