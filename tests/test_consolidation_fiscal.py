"""Independent fiscal consolidation regressions; no official submission is claimed."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from test_fiscal import fiscal_sale as fiscal_sale

from apps.billing.models import Invoice
from apps.billing.services import issue_invoice, production_guard, rectify_invoice, render_pdf
from apps.core.models import CompanySettings
from apps.pos.models import OpenTicket, Sale, TicketLine
from apps.verifactu.protocol import qr_url
from apps.verifactu.services import verify_chain

pytestmark = pytest.mark.django_db
PRODUCER = {"name": "Synthetic producer", "tax_id": "89890001K"}


def emit(fiscal_sale):
    sale, actor = fiscal_sale
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        return issue_invoice(sale, actor), actor


def test_commercial_configuration_changes_do_not_rewrite_fiscal_history(fiscal_sale):
    invoice, _ = emit(fiscal_sale)
    original_issuer = dict(invoice.issuer)
    original_record = invoice.fiscal_records.get()
    original_xml, original_hash = original_record.xml, original_record.fingerprint
    original_qr = qr_url(invoice)
    company = CompanySettings.load()
    company.name = "New legal display name"
    company.address = "New future fiscal address"
    company.timezone = "Atlantic/Canary"
    company.simplified_series = "NEXT"
    company.full_clean()
    company.save()
    invoice.refresh_from_db()
    original_record.refresh_from_db()
    assert invoice.issuer == original_issuer
    assert original_record.xml == original_xml
    assert original_record.fingerprint == original_hash
    assert qr_url(invoice) == original_qr
    assert verify_chain()
    import io

    from pypdf import PdfReader

    text = " ".join(
        page.extract_text() for page in PdfReader(io.BytesIO(render_pdf(invoice))).pages
    )
    assert "Empresa prueba" in text and "Prueba 1" in text
    assert "New legal display name" not in text and "New future fiscal address" not in text


def test_new_authorized_series_applies_only_to_future_documents(fiscal_sale):
    first, actor = emit(fiscal_sale)
    company = CompanySettings.load()
    company.simplified_series = "NEXT"
    company.full_clean()
    company.save()
    ticket = OpenTicket.objects.create(created_by=actor)
    TicketLine.objects.create(
        ticket=ticket,
        description="Future sale",
        quantity=1,
        unit_price=Decimal("12.10"),
        tax_rate=Decimal("21"),
    )
    sale = Sale.objects.create(
        ticket=ticket,
        total=Decimal("12.10"),
        created_by=actor,
        idempotency_key="future-series",
        request_fingerprint="b" * 64,
    )
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        second = issue_invoice(sale, actor)
    first.refresh_from_db()
    assert first.series == "S" and first.number == 1
    assert second.series == "NEXT" and second.number == 1
    assert verify_chain()


def test_refund_keeps_original_identity_when_commercial_settings_change(fiscal_sale):
    invoice, actor = emit(fiscal_sale)
    company = CompanySettings.load()
    company.name = "Future company name"
    company.address = "Future address"
    company.rectification_series = "RET"
    company.save()
    with override_settings(FISCAL_PRODUCER=PRODUCER):
        refund = rectify_invoice(invoice, actor, "Total return", reference="external-confirmation")
    assert refund.series == "RET" and refund.issuer == invoice.issuer
    assert refund.total == -invoice.total
    assert verify_chain()


@pytest.mark.parametrize("approved,evidence", [(False, ""), (True, "")])
def test_technical_settings_cannot_replace_external_production_gate(
    fiscal_sale, approved, evidence
):
    company = CompanySettings.load()
    company.producer_name = PRODUCER["name"]
    company.producer_tax_id = PRODUCER["tax_id"]
    with override_settings(FISCAL_PRODUCTION_APPROVED=approved, FISCAL_APPROVAL_EVIDENCE=evidence):
        with pytest.raises(ValidationError):
            production_guard(company, mode="PRODUCTION")
    assert not Invoice.objects.exists()
