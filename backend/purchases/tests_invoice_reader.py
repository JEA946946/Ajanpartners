"""Læs leverandørfakturaer lokalt (PDF-tekst og XML) og foreslå en regning."""

import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from core.testing import LedgerTestCase
from purchases import invoice_reader as r


def make_pdf(lines):
    """En tekst-PDF, som en leverandørs fakturaprogram ville lave den."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in lines:
        c.drawString(40, y, line)
        y -= 16
    c.save()
    return buf.getvalue()


INVOICE = [
    "Kontorgrej ApS",
    "Industrivej 4, 8000 Aarhus C",
    "CVR-nr. 87 65 43 21",
    "",
    "Faktura",
    "Fakturanr.: 2026-1042",
    "Fakturadato: 03-11-2026",
    "Forfaldsdato: 17.11.2026",
    "Til: Testkunde ApS  CVR 12345678",
    "Beskrivelse                Antal   Pris      Beløb",
    "Kopipapir A4 500 ark       10 stk  45,00     450,00",
    "Toner sort HP 26X          2 stk   1.275,50  2.551,00",
    "Subtotal                                     3.001,00",
    "Moms 25%                                     750,25",
    "I alt DKK                                    3.751,25",
    "Betales til +71<123456789012345+87654321<",
]


class ParseHelpersTests(LedgerTestCase):
    def test_amounts_and_dates(self):
        self.assertEqual(r.parse_amount("1.275,50"), Decimal("1275.50"))
        self.assertEqual(r.parse_amount("1,275.50"), Decimal("1275.50"))
        self.assertEqual(r.parse_date("17.11.2026").isoformat(), "2026-11-17")
        self.assertEqual(r.parse_date("3. november 2026").isoformat(), "2026-11-03")
        self.assertEqual(r.parse_date("2026-11-03").isoformat(), "2026-11-03")


class ReadPdfTests(LedgerTestCase):
    def test_text_pdf(self):
        res = r.read_invoice(make_pdf(INVOICE), "faktura.pdf", own_cvr="12345678")
        p = res["parsed"]
        self.assertEqual(res["source"], "pdf_text")
        self.assertEqual(p["supplier"]["cvr"], "87654321")      # ikke vores eget CVR
        self.assertEqual(p["supplier"]["name"], "Kontorgrej ApS")
        self.assertEqual(p["number"], "2026-1042")
        self.assertEqual((p["issue_date"], p["due_date"]), ("2026-11-03", "2026-11-17"))
        self.assertEqual((p["tax_exclusive"], p["tax_total"], p["tax_inclusive"]), ("3001.00", "750.25", "3751.25"))
        self.assertEqual(len(p["lines"]), 2)
        self.assertEqual(p["lines"][1]["unit_price"], "1275.50")
        self.assertEqual(p["lines"][1]["tax_percent"], "25")
        self.assertEqual(p["payment_id"], "+71<123456789012345+87654321<")
        self.assertEqual(res["confidence"]["totals"], "high")
        self.assertEqual(res["confidence"]["lines"], "high")
        self.assertEqual(res["warnings"], [])

    def test_buyer_cvr_is_never_the_supplier(self):
        # Også når vores eget CVR ikke er kendt (eller ved en fejl er det samme som leverandørens).
        p = r.read_invoice(make_pdf(INVOICE), "f.pdf", own_cvr="")["parsed"]
        self.assertEqual(p["supplier"]["cvr"], "87654321")
        only_buyer = [l for l in INVOICE if not l.startswith("CVR-nr.")]
        p = r.read_invoice(make_pdf(only_buyer), "f.pdf", own_cvr="")["parsed"]
        self.assertEqual(p["supplier"]["cvr"], "")

    def test_lines_including_vat_are_converted(self):
        lines = [l for l in INVOICE if not l.startswith(("Kopipapir", "Toner"))]
        lines.insert(10, "Rengøring november        1 stk   3.751,25  3.751,25")
        p = r.read_invoice(make_pdf(lines), "f.pdf", own_cvr="12345678")["parsed"]
        self.assertEqual(p["lines"][0]["unit_price"], "3001.00")

    def test_unreadable_lines_fall_back_to_one_net_line(self):
        lines = [l for l in INVOICE if not l.startswith(("Kopipapir", "Toner"))]
        res = r.read_invoice(make_pdf(lines), "f.pdf", own_cvr="12345678")
        self.assertEqual(len(res["parsed"]["lines"]), 1)
        self.assertEqual(res["parsed"]["lines"][0]["unit_price"], "3001.00")
        self.assertEqual(res["confidence"]["lines"], "low")

    def test_scanned_pdf_without_ocr_is_explained(self):
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        canvas.Canvas(buf).save()  # tom side = som en scanning uden tekstlag
        if r.ocr_available():
            self.skipTest("Tesseract er installeret")
        with self.assertRaises(r.ReadError) as cm:
            r.read_invoice(buf.getvalue(), "scan.pdf")
        self.assertIn("OCR", str(cm.exception))

    def test_ubl_xml(self):
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
 <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
 <cbc:ID>A-77</cbc:ID><cbc:IssueDate>2026-11-01</cbc:IssueDate><cbc:DocumentCurrencyCode>DKK</cbc:DocumentCurrencyCode>
 <cac:AccountingSupplierParty><cac:Party><cbc:EndpointID schemeID="0184">87654321</cbc:EndpointID>
  <cac:PartyName><cbc:Name>Kontorgrej ApS</cbc:Name></cac:PartyName></cac:Party></cac:AccountingSupplierParty>
 <cac:TaxTotal><cbc:TaxAmount currencyID="DKK">25.00</cbc:TaxAmount></cac:TaxTotal>
 <cac:LegalMonetaryTotal><cbc:LineExtensionAmount currencyID="DKK">100.00</cbc:LineExtensionAmount>
  <cbc:TaxExclusiveAmount currencyID="DKK">100.00</cbc:TaxExclusiveAmount>
  <cbc:TaxInclusiveAmount currencyID="DKK">125.00</cbc:TaxInclusiveAmount>
  <cbc:PayableAmount currencyID="DKK">125.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
 <cac:InvoiceLine><cbc:ID>1</cbc:ID><cbc:InvoicedQuantity unitCode="EA">1</cbc:InvoicedQuantity>
  <cbc:LineExtensionAmount currencyID="DKK">100.00</cbc:LineExtensionAmount>
  <cac:Item><cbc:Name>Kuglepenne</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID>
  <cbc:Percent>25</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item>
  <cac:Price><cbc:PriceAmount currencyID="DKK">100.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
</Invoice>"""
        res = r.read_invoice(xml, "f.xml")
        self.assertEqual((res["source"], res["parsed"]["number"]), ("xml", "A-77"))
        self.assertEqual(res["parsed"]["lines"][0]["description"], "Kuglepenne")


class ReadInvoiceEndpointTests(LedgerTestCase):
    def test_upload_suggests_and_links_document(self):
        from core.models import Document
        from purchases.models import Supplier
        Supplier.objects.create(code="SUP-0001", name="Kontorgrej ApS", tax_id="87654321")
        f = SimpleUploadedFile("faktura.pdf", make_pdf(INVOICE), content_type="application/pdf")
        try:
            resp = self.api.post("/api/v1/bills/read-invoice", {"file": f}, format="multipart")
        finally:
            from django.db import connection
            connection.set_tenant(self.tenant)
        self.assertEqual(resp.status_code, 200, resp.content)
        d = resp.json()["data"]
        self.assertTrue(d["read"])
        prop = d["proposal"]
        self.assertIsNotNone(prop["supplier_id"])
        self.assertEqual(prop["reference"], "2026-1042")
        self.assertEqual(len(prop["lines"]), 2)
        self.assertTrue(all(l["tax_code_id"] for l in prop["lines"]), prop["lines"])
        doc = Document.objects.get(id=d["document_id"])
        self.assertEqual(len(doc.sha256), 64)
        # Brugeren gemmer forslaget som regning → bilaget kobles på.
        acc = self.account_id_for_expense()
        payload = {"supplier_id": prop["supplier_id"], "date": prop["date"], "due_date": prop["due_date"],
                   "reference": prop["reference"], "document_id": d["document_id"],
                   "lines": [{**l, "account_id": l["account_id"] or acc} for l in prop["lines"]]}
        resp = self.post("/api/v1/bills", payload)
        self.assertEqual(resp.status_code, 201, resp.content)
        bill = resp.json()["data"]["bill"]
        self.assertEqual(Decimal(str(bill["total"])), Decimal("3751.25"))
        doc.refresh_from_db()
        self.assertEqual(str(doc.bill_id), bill["id"])

    def account_id_for_expense(self):
        from accounts.models import Account
        return str(Account.objects.filter(code__startswith="2", is_active=True).exclude(is_header=True)
                   .order_by("code").first().id)
