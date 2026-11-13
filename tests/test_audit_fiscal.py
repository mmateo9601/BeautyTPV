"""Fiscal audit regressions. All SOAP responses are synthetic, never AEAT receipts."""

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone
from test_fiscal import fiscal_sale as fiscal_sale
from test_fiscal import response_fixture

from apps.billing.services import issue_invoice, production_guard, rectify_invoice
from apps.core.models import CompanySettings
from apps.verifactu.models import FiscalEndpointState, FiscalOutbox, FiscalRecord
from apps.verifactu.protocol import fiscal_date, validate_xml, verify_record_snapshot
from apps.verifactu.services import (
    annul_record,
    correct_rejected,
    create_record,
    send_one,
    verify_chain,
)

pytestmark = pytest.mark.django_db
PRODUCER = {"name": "Fiscal audit producer", "tax_id": "89890001K"}


def issued(fiscal_sale):
    sale, actor = fiscal_sale
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        invoice = issue_invoice(sale, actor)
    return invoice, actor


def test_a_f01_verifier_compares_xml_invoice_and_hash_inputs(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    record = invoice.fiscal_records.get()
    assert verify_chain()
    assert verify_record_snapshot(record, None)
    record.xml = record.xml.replace("<sf:ImporteTotal>121.00", "<sf:ImporteTotal>1.00")
    assert not verify_record_snapshot(record, None)
    record.refresh_from_db()
    record.xml = record.xml.replace("Servicios y productos de estética", "Altered description")
    assert not verify_record_snapshot(record, None)
    record.refresh_from_db()
    record.canonical_payload += "tamper"
    assert not verify_record_snapshot(record, None)


def test_a_f01_verifier_checks_actual_chain_identity(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        refund = rectify_invoice(invoice, actor, "Total refund", reference="external-refund")
    first = invoice.fiscal_records.get()
    second = refund.fiscal_records.get()
    assert verify_record_snapshot(second, first)
    second.xml = second.xml.replace(first.fingerprint, "0" * 64)
    assert not verify_record_snapshot(second, first)


def test_a_f02_aeat_wait_is_shared_between_different_pending_records(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        second = rectify_invoice(invoice, actor, "Total refund", reference="external-refund")
    calls = []

    def transport(*args, **kwargs):
        calls.append(1)
        return SimpleNamespace(content=response_fixture(invoice), raise_for_status=lambda: None)

    with override_settings(TESTING=True):
        assert send_one(invoice.fiscal_records.get().outbox.pk, transport=transport) == "ACCEPTED"
        assert send_one(second.fiscal_records.get().outbox.pk, transport=transport) is None
    assert len(calls) == 1
    state = FiscalEndpointState.objects.get(environment="TEST")
    assert state.next_allowed_at > timezone.now() + timedelta(seconds=55)
    assert second.fiscal_records.get().outbox.attempts == 0


def test_a_f02_expired_sender_cannot_overwrite_new_lease(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    item = invoice.fiscal_records.get().outbox

    def transport(*args, **kwargs):
        FiscalOutbox.objects.filter(pk=item.pk).update(status="RETRY", lease_token="new-owner")
        FiscalEndpointState.objects.filter(environment="TEST").update(lease_token="new-owner")
        return SimpleNamespace(content=response_fixture(invoice), raise_for_status=lambda: None)

    with override_settings(TESTING=True):
        assert send_one(item.pk, transport=transport) == "LEASE_LOST"
    item.refresh_from_db()
    assert item.status == "RETRY" and item.lease_token == "new-owner"
    assert item.transmissions.count() == 1


def test_a_f03_production_guard_cannot_be_bypassed_by_test_company(fiscal_sale):
    company = CompanySettings.load()
    assert company.fiscal_mode == "TEST"
    with override_settings(FISCAL_PRODUCTION_APPROVED=False):
        with pytest.raises(ValidationError):
            production_guard(company, mode="PRODUCTION")
    invoice, actor = issued(fiscal_sale)
    invoice.fiscal_mode = "PRODUCTION"
    with override_settings(FISCAL_PRODUCTION_APPROVED=False):
        with pytest.raises(ValidationError):
            create_record(invoice)
        with pytest.raises(ValidationError):
            rectify_invoice(invoice, actor, "Refund", reference="confirmed")
    assert FiscalRecord.objects.count() == 1


def test_a_f04_extended_response_status_fits_model_validation(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    item = invoice.fiscal_records.get().outbox
    for status in ["ACCEPTED_WITH_ERRORS", "DUPLICATE_REVIEW"]:
        item.status = status
        item.full_clean()


def test_a_f05_rejected_annulment_stays_an_annulment(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    actor.role = "ADMIN"
    actor.save()
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        original = invoice.fiscal_records.get()
        annulment = annul_record(original, actor, "No real sale", without_previous=True)
        FiscalOutbox.objects.filter(record=annulment).update(status="REJECTED")
        corrected = correct_rejected(annulment, actor)
    assert corrected.record_type == "ANULACION"
    assert "<sf:RechazoPrevio>S</sf:RechazoPrevio>" in corrected.xml
    assert "<sf:SinRegistroPrevio>S</sf:SinRegistroPrevio>" in annulment.xml
    assert validate_xml(annulment.xml) and validate_xml(corrected.xml)
    assert verify_chain()


def test_a_f06_invoice_date_and_number_year_follow_snapshot_timezone(fiscal_sale, monkeypatch):
    monkeypatch.setattr(
        "apps.billing.services.timezone.now",
        lambda: datetime(2025, 12, 31, 23, 30, tzinfo=dt_timezone.utc),
    )
    invoice, actor = issued(fiscal_sale)
    invoice.refresh_from_db()
    assert invoice.year == 2026
    assert fiscal_date(invoice) == "01-01-2026"
    assert "FechaExpedicionFactura=01-01-2026" in invoice.fiscal_records.get().canonical_payload


def test_a_f07_bad_cash_session_input_is_a_validation_error_not_500(fiscal_sale, client):
    invoice, actor = issued(fiscal_sale)
    client.force_login(actor)
    response = client.post(
        f"/facturas/{invoice.pk}/rectificar/",
        {"cash_session": "not-an-integer", "method": "CASH", "reason": "Return"},
    )
    assert response.status_code == 302
    assert not invoice.rectifications.exists()


def test_a_f08_rejected_record_status_is_refetched_before_correction(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    actor.role = "ADMIN"
    actor.save()
    record = invoice.fiscal_records.get()
    FiscalOutbox.objects.filter(record=record).update(status="REJECTED")
    assert record.outbox.status == "REJECTED"
    FiscalOutbox.objects.filter(record=record).update(status="ACCEPTED")
    with pytest.raises(ValidationError):
        correct_rejected(record, actor)
    assert invoice.fiscal_records.count() == 1


@pytest.mark.parametrize(
    "table",
    [
        "billing_invoice",
        "billing_invoiceline",
        "billing_refund",
        "verifactu_fiscalrecord",
        "verifactu_fiscaltransmission",
    ],
)
def test_a_f09_sqlite_replace_cannot_rewrite_issued_rows(fiscal_sale, table):
    from django.db import IntegrityError, connection, transaction

    from apps.verifactu.models import FiscalTransmission

    invoice, actor = issued(fiscal_sale)
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        rectify_invoice(invoice, actor, "Refund", reference="confirmed")
    FiscalTransmission.objects.create(outbox=invoice.fiscal_records.get().outbox, status="RETRY")
    with connection.cursor() as cursor:
        columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        pk = cursor.execute(f"SELECT id FROM {table} LIMIT 1").fetchone()[0]
    quoted = ",".join('"' + column + '"' for column in columns)
    with pytest.raises(IntegrityError), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT OR REPLACE INTO {table} ({quoted}) SELECT {quoted} FROM {table} WHERE id=%s",
                [pk],
            )
    assert verify_chain()


def test_a_f10_response_operation_must_match_sent_record(fiscal_sale):
    from apps.verifactu.protocol import validate_response

    invoice, actor = issued(fiscal_sale)
    content = response_fixture(invoice)
    with pytest.raises(ValueError):
        validate_response(content, invoice, record_type="ANULACION")
    assert validate_response(content, invoice)


def test_a_f11_each_record_freezes_its_actual_generating_software_version(fiscal_sale, monkeypatch):
    monkeypatch.setattr("apps.support.versioning.application_version", lambda **kwargs: "1.2.3")
    invoice, actor = issued(fiscal_sale)
    monkeypatch.setattr("apps.support.versioning.application_version", lambda **kwargs: "9.9.9")
    original = invoice.fiscal_records.get()
    FiscalOutbox.objects.filter(record=original).update(status="REJECTED")
    actor.role = "ADMIN"
    actor.save()
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        corrected = correct_rejected(original, actor)
    assert "<sf:Version>9.9.9</sf:Version>" in corrected.xml
    original.refresh_from_db()
    assert "<sf:Version>1.2.3</sf:Version>" in original.xml
    assert "9.9.9" not in original.xml


def test_a_f12_accepted_with_errors_uses_subsanacion_without_rechazo(fiscal_sale):
    invoice, actor = issued(fiscal_sale)
    actor.role = "ADMIN"
    actor.save()
    original = invoice.fiscal_records.get()
    FiscalOutbox.objects.filter(record=original).update(status="ACCEPTED_WITH_ERRORS")
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        corrected = correct_rejected(original, actor)
    assert "<sf:Subsanacion>S</sf:Subsanacion>" in corrected.xml
    assert "RechazoPrevio" not in corrected.xml
    assert validate_xml(corrected.xml)
    assert original.outbox.status == "ACCEPTED_WITH_ERRORS"
    assert verify_chain()


def test_a_f13_producer_configuration_can_be_corrected_without_rewriting_origin(fiscal_sale):
    sale, actor = fiscal_sale
    invoice = issue_invoice(sale, actor)
    original = invoice.fiscal_records.get()
    old_xml = original.xml
    company = CompanySettings.load()
    company.producer_name = "Configured actual producer"
    company.producer_tax_id = "89890001K"
    company.save()
    actor.role = "ADMIN"
    actor.save()
    FiscalOutbox.objects.filter(record=original).update(status="REJECTED")
    corrected = correct_rejected(original, actor)
    assert validate_xml(corrected.xml)
    assert "Configured actual producer" in corrected.xml
    original.refresh_from_db()
    assert original.xml == old_xml
    assert invoice.fiscal_records.count() == 2


def test_a_f03_old_production_outbox_still_requires_approval_after_mode_switch(fiscal_sale):
    sale, actor = fiscal_sale
    company = CompanySettings.load()
    company.fiscal_mode = "PRODUCTION"
    company.producer_name = PRODUCER["name"]
    company.producer_tax_id = PRODUCER["tax_id"]
    company.save()
    with override_settings(
        FISCAL_PRODUCTION_APPROVED=True,
        FISCAL_APPROVAL_EVIDENCE="synthetic-unit-test-only",
        FISCAL_PRODUCER=PRODUCER,
    ):
        invoice = issue_invoice(sale, actor)
    company.fiscal_mode = "TEST"
    company.save()
    called = []
    with override_settings(TESTING=True, FISCAL_PRODUCTION_APPROVED=False):
        assert (
            send_one(
                invoice.fiscal_records.get().outbox.pk,
                transport=lambda *args, **kwargs: called.append(True),
            )
            == "RETRY"
        )
    assert called == []
    assert invoice.fiscal_records.get().outbox.status == "RETRY"


def test_technical_annulment_http_preserves_sale_and_records_reason(fiscal_sale, client):
    from apps.accounts.models import User
    from apps.audit.models import AuditEvent
    from apps.billing.models import Refund
    from apps.support.models import SupportSession

    company = CompanySettings.load()
    company.producer_name = PRODUCER["name"]
    company.producer_tax_id = PRODUCER["tax_id"]
    company.save()
    invoice, actor = issued(fiscal_sale)
    original = invoice.fiscal_records.get()
    technician = User.objects.create_user(username="annul-tech", role="SUPERADMIN")
    SupportSession.objects.create(
        actor=technician,
        approved_by=technician,
        justification="Registro de prueba emitido por error",
        scope="TECHNICAL",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    client.force_login(technician)
    session = client.session
    session["elevated_until"] = timezone.now().timestamp() + 600
    session.save()
    response = client.post(
        f"/soporte/fiscal/{original.outbox.pk}/anular/",
        {
            "confirmation": "ANULAR REGISTRO",
            "reason": "Registro de prueba emitido por error",
            "without_previous": "1",
        },
    )
    assert response.status_code == 302
    annulment = invoice.fiscal_records.get(record_type="ANULACION")
    assert validate_xml(annulment.xml)
    assert not Refund.objects.exists()
    assert invoice.total == Decimal("121.00")
    assert (
        AuditEvent.objects.get(action="fiscal.annul").metadata["reason"]
        == "Registro de prueba emitido por error"
    )
