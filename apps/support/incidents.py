"""Operational incidents with a separate, append-only intervention history."""

import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.audit.services import record
from apps.core.transactions import atomic_retry

from .models import Incident, IncidentAction
from .services import require_authorization


def incident_text(value, limit):
    value = str(value or "").strip()
    if not value or len(value) > limit:
        raise ValidationError(f"Escriba una descripcion entre 1 y {limit} caracteres.")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ValidationError("No se admiten caracteres de control.")
    sensitive = (
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        r"\b(?:\d[ -]?){13,19}\b",
        r"\b\d{8}[A-Za-z]\b",
        r"\b(?:password|contrase[nñ]a|pin|token|secret|authorization)\s*[:=]",
        r"<\s*[!?/A-Za-z]",
        r"-----BEGIN",
        r"\bBearer\s+\S+",
    )
    if any(re.search(pattern, value, re.IGNORECASE) for pattern in sensitive):
        raise ValidationError(
            "No incluya datos personales, tarjetas, XML, credenciales ni logs. Describa el problema sin identificadores."
        )
    return value


def authorize_incident(actor, category=None):
    require_role(actor, "MANAGER")
    if actor.role == "SUPERADMIN":
        require_authorization(actor)
    elif category and category != Incident.Category.OPERATIONAL:
        raise PermissionDenied("Las incidencias tecnicas requieren soporte autorizado.")


def visible_incidents(actor):
    authorize_incident(actor)
    query = Incident.objects.select_related("created_by")
    if actor.role != "SUPERADMIN":
        query = query.filter(category=Incident.Category.OPERATIONAL)
    return query


@atomic_retry
def create_incident(actor, *, title, description, category="OPERATIONAL", severity="MEDIUM"):
    authorize_incident(actor, category)
    incident = Incident(
        title=incident_text(title, 160),
        description=incident_text(description, 1000),
        category=category,
        severity=severity,
        created_by=actor,
    )
    incident.full_clean()
    incident.save()
    record(actor, "incident.created", obj=incident, metadata={"status": incident.status})
    return incident


@atomic_retry
def add_action(actor, incident, *, note, status, category, severity, version):
    incident = Incident.objects.get(pk=incident.pk)
    authorize_incident(actor, incident.category)
    authorize_incident(actor, category)
    note = incident_text(note, 1000)
    if type(version) is not int or version < 0:
        raise ValidationError("Version no valida; vuelva a abrir la incidencia.")
    allowed = {
        "OPEN": {"OPEN", "IN_PROGRESS", "RESOLVED"},
        "IN_PROGRESS": {"IN_PROGRESS", "RESOLVED"},
        "RESOLVED": {"RESOLVED", "OPEN"},
    }
    if status not in allowed[incident.status]:
        raise ValidationError(
            "Transicion no permitida. Reabra una incidencia resuelta antes de tramitarla."
        )
    if category not in Incident.Category.values or severity not in Incident.Severity.values:
        raise ValidationError("Clasificacion no valida.")
    now = timezone.now()
    resolved = (incident.resolved_at or now) if status == "RESOLVED" else None
    changed = Incident.objects.filter(pk=incident.pk, version=version).update(
        status=status,
        category=category,
        severity=severity,
        resolved_at=resolved,
        updated_at=now,
        version=F("version") + 1,
    )
    if changed != 1:
        raise ValidationError("Otra persona actualizo la incidencia. Recargue antes de guardar.")
    action = IncidentAction.objects.create(
        incident=incident,
        actor=actor,
        note=note,
        previous_status=incident.status,
        new_status=status,
        previous_category=incident.category,
        new_category=category,
        previous_severity=incident.severity,
        new_severity=severity,
    )
    record(actor, "incident.action", obj=action, metadata={"status": status})
    incident.refresh_from_db()
    return incident
