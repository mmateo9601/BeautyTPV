"""Commercial settings are frozen at issue time, including printed text."""

import io

import pytest
from django.test import override_settings
from pypdf import PdfReader
from test_fiscal import fiscal_sale as fiscal_sale

from apps.billing.services import issue_invoice, rectify_invoice, render_pdf
from apps.core.models import CompanySettings
from apps.hardware.escpos import render_receipt
from apps.verifactu.services import verify_chain

pytestmark = pytest.mark.django_db


def test_receipt_commercial_data_is_frozen_for_pdf_copy_and_refund(fiscal_sale):
    sale, actor = fiscal_sale
    company = CompanySettings.load()
    company.trade_name = "Salon Primavera"
    company.commercial_address = "Calle comercial 12"
    company.phone = "910000000"
    company.email = "salon@example.invalid"
    company.ticket_footer = "Gracias por su visita <texto>"
    company.save()
    producer = {"name": "Productor de pruebas", "tax_id": "89890001K"}
    with override_settings(FISCAL_PRODUCER=producer):
        invoice = issue_invoice(sale, actor)
    snapshot = dict(invoice.issuer)
    original_bytes = render_receipt(invoice, copy=True)
    company.trade_name = "Nombre futuro"
    company.phone = "920000000"
    company.ticket_footer = "Mensaje futuro"
    company.save()
    invoice.refresh_from_db()
    assert invoice.issuer == snapshot
    assert render_receipt(invoice, copy=True) == original_bytes
    assert b"Salon Primavera" in original_bytes
    assert b"Gracias por su visita <texto>" in original_bytes
    text = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(render_pdf(invoice))).pages)
    assert "Salon Primavera" in text and "910000000" in text
    assert "Gracias por su visita <texto>" in text
    assert "Mensaje futuro" not in text and "Nombre futuro" not in text
    with override_settings(FISCAL_PRODUCER=producer):
        refund = rectify_invoice(invoice, actor, "Devolucion completa", reference="EXTERNAL-REFUND")
    assert refund.issuer == snapshot
    assert b"Salon Primavera" in render_receipt(refund)
    assert verify_chain()
