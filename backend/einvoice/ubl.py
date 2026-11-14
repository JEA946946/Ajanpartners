"""Dannelse af UBL 2.1-fakturaer: Peppol BIS Billing 3.0 og OIOUBL 2.1.

``build_invoice(invoice, fmt)`` og ``build_credit_note(credit_note, fmt)`` giver
XML som tekst ud fra sales.models.Invoice/CreditNote. Modellerne læses kun.

Elementernes rækkefølge følger UBL 2.1-skemaerne (xsd:sequence), og de
obligatoriske Peppol-elementer er med: CustomizationID, ProfileID, ID,
IssueDate, (Invoice|CreditNote)TypeCode, DocumentCurrencyCode, BuyerReference,
AccountingSupplierParty/AccountingCustomerParty med EndpointID (schemeID 0184
for CVR, 0088 for GLN), TaxTotal, LegalMonetaryTotal og linjer.

Validering: einvoice/tests_schematron.py kører UBL 2.1 XSD, CEN EN 16931- og Peppol BIS 3.0-
schematron samt Erhvervsstyrelsens OIOUBL 2.1-schematron på de dannede dokumenter
(artefakterne og deres kilder: einvoice/validation/SOURCES.txt).
OIOUBL 2.1 dannes af ``_oioubl_document`` (danske kodelister, schemeAgencyID 320) og
valideres mod Erhvervsstyrelsens OIOUBL-schematron i einvoice/tests_schematron.py.
"""

import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CREDIT_NOTE = "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

ET.register_namespace("cac", NS_CAC)
ET.register_namespace("cbc", NS_CBC)

PROFILES = {
    "peppol": {
        "customization": "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
        "profile": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
        "ubl_version": None,
    },
    "oioubl": {
        # Verificeret mod Erhvervsstyrelsens OIOUBL 2.1-schematron v1.17.2 (einvoice/validation/oioubl/).
        "customization": "OIOUBL-2.1",
        "profile": "urn:www.nesubl.eu:profiles:profile5:ver2.0",
        "profile_scheme": "urn:oioubl:id:profileid-1.2",
        "ubl_version": "2.1",
    },
}

SCHEME_CVR = "0184"   # ISO 6523 ICD: Danish CVR (DK:CVR)
SCHEME_GLN = "0088"   # ISO 6523 ICD: GS1 GLN
UNIT_EACH = "C62"     # UN/ECE rec. 20: "one"
TWO = Decimal("0.01")

EXEMPTION = {
    "E": (None, "Momsfritaget, jf. momslovens § 13"),
    "AE": ("VATEX-EU-AE", "Omvendt betalingspligt"),
    "G": ("VATEX-EU-G", "Eksport uden for EU"),
    "K": ("VATEX-EU-IC", "Momsfri levering til andet EU-land"),
}


def money(value):
    return Decimal(str(value or 0)).quantize(TWO, rounding=ROUND_HALF_UP)


def fmt_amount(value):
    return f"{money(value):.2f}"


def fmt_qty(value):
    q = Decimal(str(value or 0)).normalize()
    return f"{q:f}"


def digits(value):
    return re.sub(r"\D", "", str(value or ""))


def valid_gln(gln):
    """GS1-kontrolciffer (Peppol PEPPOL-COMMON-R040)."""
    gln = digits(gln)
    if len(gln) != 13:
        return False
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(gln[:12])))
    return (10 - total % 10) % 10 == int(gln[12])


def endpoint_for(cvr="", gln=""):
    """(schemeID, id) for en part: GLN hvis gyldigt, ellers CVR."""
    gln = digits(gln)
    if valid_gln(gln):
        return SCHEME_GLN, gln
    cvr = digits(cvr)
    if len(cvr) == 8:
        return SCHEME_CVR, cvr
    return None, None


def split_address(text):
    """Fritekstadresse → (gade, postnr., by). "Testvej 1\n2100 København Ø"."""
    lines = [l.strip() for l in re.split(r"[\n,]", text or "") if l.strip()]
    street, zip_code, city = "", "", ""
    for line in lines:
        m = re.match(r"^(?:DK-?)?(\d{4})\s+(.+)$", line)
        if m and not zip_code:
            zip_code, city = m.group(1), m.group(2)
        elif not street:
            street = line
    return street, zip_code, city


def tax_category(tax_code):
    """(kategori, sats) ud fra core.TaxCode (rubrik/omvendt betaling, ellers tekst)."""
    if tax_code is None:
        return "E", Decimal("0")
    rate = Decimal(str(tax_code.rate or 0))
    if rate > 0:
        return "S", rate
    rubrik = getattr(tax_code, "rubrik", "") or ""
    reverse = getattr(tax_code, "reverse_charge", "") or ""
    if rubrik in ("B_goods", "B_goods_other"):
        return "K", Decimal("0")          # momsfri levering af varer til andet EU-land
    if rubrik == "B_services" or reverse:
        return "AE", Decimal("0")         # køber afregner momsen (omvendt betalingspligt)
    text = f"{tax_code.code} {tax_code.name}".lower()
    if any(k in text for k in ("omvendt", "reverse")):
        return "AE", Decimal("0")
    if rubrik == "C" and any(k in text for k in ("eksport", "export", "udenfor eu", "uden for eu")):
        return "G", Decimal("0")
    return "E", Decimal("0")


@dataclass
class Party:
    name: str
    cvr: str = ""
    gln: str = ""
    street: str = ""
    zip_code: str = ""
    city: str = ""
    country: str = "DK"
    email: str = ""
    phone: str = ""
    vat_registered: bool = True

    @property
    def endpoint(self):
        return endpoint_for(self.cvr, self.gln)


@dataclass
class Line:
    description: str
    quantity: Decimal
    unit_price: Decimal
    category: str
    percent: Decimal

    @property
    def amount(self):
        return money(self.quantity * self.unit_price)


class EInvoiceError(Exception):
    pass


# --- Indsamling af data fra modellerne -------------------------------------

def supplier_party():
    """Afsenderen: kunden selv (CompanySettings + ClientCompany for skemaet)."""
    from django.db import connection

    from core.models import CompanySettings

    cs = CompanySettings.objects.first()
    tenant = getattr(connection, "tenant", None)
    name = (getattr(cs, "company_name", "") or getattr(tenant, "name", "") or "").strip()
    cvr = digits(getattr(tenant, "cvr", "") or getattr(cs, "tax_id", ""))
    street, zip_code, city = split_address(getattr(tenant, "address", "") or getattr(cs, "address", ""))
    zip_code = getattr(tenant, "zip_code", "") or zip_code
    city = getattr(tenant, "city", "") or getattr(cs, "city", "") or city
    return Party(name=name, cvr=cvr, gln=getattr(tenant, "gln", "") or getattr(cs, "gln", ""),
                 street=street, zip_code=zip_code, city=city,
                 email=getattr(cs, "email", "") or getattr(tenant, "email", ""),
                 phone=getattr(cs, "phone", "") or getattr(tenant, "phone", ""),
                 vat_registered=getattr(tenant, "vat_period", "quarter") != "none")


def customer_party(customer):
    street, zip_code, city = split_address(customer.address)
    tax_id = (customer.tax_id or "").replace(" ", "")
    country = (getattr(customer, "country", "") or getattr(customer, "country_code", "") or
               (tax_id[:2].upper() if tax_id[:2].isalpha() else "DK"))[:2].upper()
    cvr = getattr(customer, "cvr", "") or (tax_id if country == "DK" else "")
    return Party(name=customer.name, cvr=cvr,
                 gln=getattr(customer, "gln", "") or getattr(customer, "ean", ""),
                 street=getattr(customer, "street", "") or street,
                 zip_code=getattr(customer, "postal_code", "") or getattr(customer, "zip_code", "") or zip_code,
                 city=getattr(customer, "city", "") or city, country=country,
                 email=customer.email or "", phone=customer.phone or "",
                 vat_registered=getattr(customer, "is_business", True))


def _company_bank():
    from core.models import CompanySettings

    cs = CompanySettings.objects.first()
    return {"iban": getattr(cs, "iban", "") or "", "bic": getattr(cs, "bic", "") or getattr(cs, "swift", "") or "",
            "reg_no": getattr(cs, "bank_reg_no", "") or "", "account_no": getattr(cs, "bank_account_no", "") or ""}


def invoice_lines(invoice):
    lines = []
    for l in invoice.lines.select_related("tax_code").all():
        if l.is_text:
            continue
        cat, pct = tax_category(l.tax_code)
        qty, price = Decimal(str(l.quantity)), Decimal(str(l.unit_price))
        if price < 0:  # Peppol BR-27: prisen må ikke være negativ – vend fortegnet over på antallet
            qty, price = -qty, -price
        lines.append(Line(l.description or "Vare/ydelse", qty, price, cat, pct))
    if not lines:  # faktura uden varelinjer: én linje med beløbet
        lines.append(_single_line(invoice.subtotal, invoice.tax_amount, invoice.notes or "Ydelse"))
    return lines


def _single_line(subtotal, tax_amount, text):
    subtotal, tax_amount = money(subtotal), money(tax_amount)
    if subtotal and tax_amount:
        pct = (tax_amount / subtotal * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return Line(text[:500], Decimal("1"), subtotal, "S", pct)
    return Line(text[:500], Decimal("1"), subtotal, "E", Decimal("0"))


def tax_breakdown(lines):
    """OrderedDict (kategori, sats) → (grundlag, moms). Moms beregnes pr. kategori (BR-CO-17)."""
    groups = OrderedDict()
    for l in lines:
        key = (l.category, l.percent)
        groups[key] = groups.get(key, Decimal("0")) + l.amount
    return OrderedDict((k, (money(base), money(base * k[1] / 100))) for k, base in groups.items())


# --- XML ---------------------------------------------------------------------

def _cbc(parent, tag, text=None, **attrs):
    el = ET.SubElement(parent, f"{{{NS_CBC}}}{tag}", {k: str(v) for k, v in attrs.items() if v not in (None, "")})
    if text is not None:
        el.text = str(text)
    return el


def _cac(parent, tag):
    return ET.SubElement(parent, f"{{{NS_CAC}}}{tag}")


def _amount(parent, tag, value, currency):
    return _cbc(parent, tag, fmt_amount(value), currencyID=currency)


def _party(parent, wrapper, p, require_endpoint=True):
    scheme, endpoint = p.endpoint
    if require_endpoint and not endpoint:
        who = "Afsenderen" if wrapper == "AccountingSupplierParty" else f"Kunden {p.name}"
        raise EInvoiceError(f"{who} mangler CVR-nummer eller GLN/EAN-nummer.")
    party = _cac(_cac(parent, wrapper), "Party")
    _cbc(party, "EndpointID", endpoint, schemeID=scheme)
    if scheme == SCHEME_GLN and len(digits(p.cvr)) == 8:
        _cbc(_cac(party, "PartyIdentification"), "ID", digits(p.cvr), schemeID=SCHEME_CVR)
    _cbc(_cac(party, "PartyName"), "Name", p.name)
    addr = _cac(party, "PostalAddress")
    if p.street:
        _cbc(addr, "StreetName", p.street)
    if p.city:
        _cbc(addr, "CityName", p.city)
    if p.zip_code:
        _cbc(addr, "PostalZone", p.zip_code)
    _cbc(_cac(addr, "Country"), "IdentificationCode", p.country or "DK")
    cvr = digits(p.cvr)
    if cvr and p.vat_registered:
        ts = _cac(party, "PartyTaxScheme")
        _cbc(ts, "CompanyID", f"{p.country or 'DK'}{cvr}")
        _cbc(_cac(ts, "TaxScheme"), "ID", "VAT")
    le = _cac(party, "PartyLegalEntity")
    _cbc(le, "RegistrationName", p.name)
    if cvr:
        _cbc(le, "CompanyID", cvr, schemeID=SCHEME_CVR)
    if p.email or p.phone:
        contact = _cac(party, "Contact")
        if p.phone:
            _cbc(contact, "Telephone", p.phone)
        if p.email:
            _cbc(contact, "ElectronicMail", p.email)
    return party


def _tax_category(parent, tag, category, percent, with_reason):
    cat = _cac(parent, tag)
    _cbc(cat, "ID", category)
    _cbc(cat, "Percent", fmt_qty(percent) if percent else "0")
    if with_reason and category in EXEMPTION:
        code, text = EXEMPTION[category]
        if code:
            _cbc(cat, "TaxExemptionReasonCode", code)
        _cbc(cat, "TaxExemptionReason", text)
    _cbc(_cac(cat, "TaxScheme"), "ID", "VAT")


def _payment_means(root, number):
    bank = _company_bank()
    if bank["iban"]:
        code, account_id = "58", bank["iban"].replace(" ", "")
    elif bank["reg_no"] and bank["account_no"]:
        code, account_id = "31", digits(bank["reg_no"]) + digits(bank["account_no"])
    else:
        return
    pm = _cac(root, "PaymentMeans")
    _cbc(pm, "PaymentMeansCode", code)
    _cbc(pm, "PaymentID", number)
    acct = _cac(pm, "PayeeFinancialAccount")
    _cbc(acct, "ID", account_id)
    if bank["bic"]:
        _cbc(_cac(acct, "FinancialInstitutionBranch"), "ID", bank["bic"])


def _document(kind, fmt, *, number, issue_date, due_date, currency, note, buyer_reference,
              billing_reference, supplier, customer, lines, payment_terms_days=None):
    if fmt not in PROFILES:
        raise EInvoiceError(f"Ukendt e-fakturaformat: {fmt}")
    if fmt == "oioubl":
        return _oioubl_document(kind, number=number, issue_date=issue_date, due_date=due_date, currency=currency,
                                note=note, billing_reference=billing_reference, supplier=supplier,
                                customer=customer, lines=lines)
    profile = PROFILES[fmt]
    ns = NS_INVOICE if kind == "invoice" else NS_CREDIT_NOTE
    root = ET.Element(f"{{{ns}}}{'Invoice' if kind == 'invoice' else 'CreditNote'}")
    if profile["ubl_version"]:
        _cbc(root, "UBLVersionID", profile["ubl_version"])
    _cbc(root, "CustomizationID", profile["customization"])
    _cbc(root, "ProfileID", profile["profile"])
    _cbc(root, "ID", number)
    _cbc(root, "IssueDate", issue_date.isoformat())
    if kind == "invoice":
        if due_date:
            _cbc(root, "DueDate", due_date.isoformat())
        _cbc(root, "InvoiceTypeCode", "380")
    else:
        _cbc(root, "CreditNoteTypeCode", "381")
    if note:
        _cbc(root, "Note", note[:1000])
    _cbc(root, "DocumentCurrencyCode", currency)
    _cbc(root, "BuyerReference", buyer_reference or number)
    if billing_reference:
        _cbc(_cac(_cac(root, "BillingReference"), "InvoiceDocumentReference"), "ID", billing_reference)
    _party(root, "AccountingSupplierParty", supplier)
    _party(root, "AccountingCustomerParty", customer)
    if kind == "invoice":
        _payment_means(root, number)
        if payment_terms_days:
            _cbc(_cac(root, "PaymentTerms"), "Note", f"Netto {payment_terms_days} dage")

    breakdown = tax_breakdown(lines)
    line_total = money(sum((l.amount for l in lines), Decimal("0")))
    tax_total = money(sum((t for _, t in breakdown.values()), Decimal("0")))
    tt = _cac(root, "TaxTotal")
    _amount(tt, "TaxAmount", tax_total, currency)
    for (cat, pct), (base, tax) in breakdown.items():
        sub = _cac(tt, "TaxSubtotal")
        _amount(sub, "TaxableAmount", base, currency)
        _amount(sub, "TaxAmount", tax, currency)
        _tax_category(sub, "TaxCategory", cat, pct, with_reason=True)

    lmt = _cac(root, "LegalMonetaryTotal")
    _amount(lmt, "LineExtensionAmount", line_total, currency)
    _amount(lmt, "TaxExclusiveAmount", line_total, currency)
    _amount(lmt, "TaxInclusiveAmount", line_total + tax_total, currency)
    _amount(lmt, "PayableAmount", line_total + tax_total, currency)

    line_tag, qty_tag = ("InvoiceLine", "InvoicedQuantity") if kind == "invoice" else \
        ("CreditNoteLine", "CreditedQuantity")
    for i, l in enumerate(lines, start=1):
        el = _cac(root, line_tag)
        _cbc(el, "ID", i)
        _cbc(el, qty_tag, fmt_qty(l.quantity), unitCode=UNIT_EACH)
        _amount(el, "LineExtensionAmount", l.amount, currency)
        item = _cac(el, "Item")
        _cbc(item, "Name", (l.description or "Vare/ydelse")[:200])
        _tax_category(item, "ClassifiedTaxCategory", l.category, l.percent, with_reason=False)
        price = _cac(el, "Price")
        _amount(price, "PriceAmount", l.unit_price, currency)

    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


# --- OIOUBL 2.1 ----------------------------------------------------------------
# OIOUBL er en dansk profil med egne kodelister (schemeAgencyID 320) og nogle afvigelser
# fra EN 16931, fx at LegalMonetaryTotal/TaxExclusiveAmount er momsbeløbet (F-INV127), og at
# hver linje har sin egen TaxTotal (F-INV138).

OIO_TAXCAT = {  # kategori → (OIOUBL-kode, kodeliste)
    "S": ("StandardRated", "urn:oioubl:id:taxcategoryid-1.1"),
    "E": ("ZeroRated", "urn:oioubl:id:taxcategoryid-1.1"),
    "AE": ("ReverseCharge", "urn:oioubl:id:taxcategoryid-1.1"),
    "K": ("K", "urn:oioubl:id:taxcategoryid-1.4"),
    "G": ("G", "urn:oioubl:id:taxcategoryid-1.4"),
}


def _oio_id(parent, tag, p):
    gln = digits(p.gln)
    if valid_gln(gln):
        return _cbc(parent, tag, gln, schemeAgencyID="9", schemeID="GLN")
    cvr = digits(p.cvr)
    if len(cvr) == 8:
        return _cbc(parent, tag, f"DK{cvr}", schemeID="DK:CVR")
    return None


def _oio_tax_scheme(parent):
    ts = _cac(parent, "TaxScheme")
    _cbc(ts, "ID", "63", schemeAgencyID="320", schemeID="urn:oioubl:id:taxschemeid-1.1")
    _cbc(ts, "Name", "Moms")


def _oio_tax_category(parent, category, percent):
    code, scheme = OIO_TAXCAT.get(category, OIO_TAXCAT["E"])
    cat = _cac(parent, "TaxCategory")
    _cbc(cat, "ID", code, schemeAgencyID="320", schemeID=scheme)
    _cbc(cat, "Percent", fmt_qty(percent) if percent else "0")
    _oio_tax_scheme(cat)


def _oio_party(root, wrapper, p, contact_id):
    party = _cac(_cac(root, wrapper), "Party")
    if _oio_id(party, "EndpointID", p) is None:
        who = "Afsenderen" if wrapper == "AccountingSupplierParty" else f"Kunden {p.name}"
        raise EInvoiceError(f"{who} mangler CVR-nummer eller GLN/EAN-nummer.")
    _oio_id(_cac(party, "PartyIdentification"), "ID", p)
    _cbc(_cac(party, "PartyName"), "Name", p.name)
    addr = _cac(party, "PostalAddress")
    _cbc(addr, "AddressFormatCode", "StructuredDK", listAgencyID="320",
         listID="urn:oioubl:codelist:addressformatcode-1.1")
    m = re.match(r"^(.*?)\s+(\d+\S*)$", p.street or "")
    street, number = (m.group(1), m.group(2)) if m else (p.street, "")
    if not (street and number and p.zip_code):
        who = "Afsenderens" if wrapper == "AccountingSupplierParty" else f"Kunden {p.name}s"
        raise EInvoiceError(f"{who} adresse skal have gade, husnummer og postnummer for at kunne sendes som OIOUBL.")
    if street:
        _cbc(addr, "StreetName", street)
    if number:
        _cbc(addr, "BuildingNumber", number)
    if p.city:
        _cbc(addr, "CityName", p.city)
    if p.zip_code:
        _cbc(addr, "PostalZone", p.zip_code)
    _cbc(_cac(addr, "Country"), "IdentificationCode", p.country or "DK")
    cvr = digits(p.cvr)
    if cvr and p.vat_registered:
        ts = _cac(party, "PartyTaxScheme")
        _cbc(ts, "CompanyID", f"DK{cvr}", schemeID="DK:SE")
        _oio_tax_scheme(ts)
    if cvr:
        le = _cac(party, "PartyLegalEntity")
        _cbc(le, "RegistrationName", p.name)
        _cbc(le, "CompanyID", f"DK{cvr}", schemeID="DK:CVR")
    contact = _cac(party, "Contact")  # påkrævet for køber (F-INV046)
    _cbc(contact, "ID", contact_id)
    if p.phone:
        _cbc(contact, "Telephone", p.phone)
    if p.email:
        _cbc(contact, "ElectronicMail", p.email)


def _oio_tax_total(parent, breakdown, currency):
    tt = _cac(parent, "TaxTotal")
    _amount(tt, "TaxAmount", sum((t for _, t in breakdown.values()), Decimal("0")), currency)
    for (cat, pct), (base, tax) in breakdown.items():
        sub = _cac(tt, "TaxSubtotal")
        _amount(sub, "TaxableAmount", base, currency)
        _amount(sub, "TaxAmount", tax, currency)
        _oio_tax_category(sub, cat, pct)


def _oio_payment(root, number, due_date, currency, payable):
    bank = _company_bank()
    means_id = None
    if bank["reg_no"] and bank["account_no"] or bank["iban"]:
        means_id = "1"
        pm = _cac(root, "PaymentMeans")
        _cbc(pm, "ID", means_id)
        if bank["reg_no"] and bank["account_no"]:
            _cbc(pm, "PaymentMeansCode", "42")
            if due_date:
                _cbc(pm, "PaymentDueDate", due_date.isoformat())
            _cbc(pm, "PaymentChannelCode", "DK:BANK", listAgencyID="320",
                 listID="urn:oioubl:codelist:paymentchannelcode-1.1")
            acct = _cac(pm, "PayeeFinancialAccount")
            _cbc(acct, "ID", digits(bank["account_no"]))
            _cbc(acct, "PaymentNote", number)
            _cbc(_cac(acct, "FinancialInstitutionBranch"), "ID", digits(bank["reg_no"]))
        else:
            _cbc(pm, "PaymentMeansCode", "31")
            if due_date:
                _cbc(pm, "PaymentDueDate", due_date.isoformat())
            _cbc(pm, "PaymentChannelCode", "IBAN", listAgencyID="320",
                 listID="urn:oioubl:codelist:paymentchannelcode-1.1")
            acct = _cac(pm, "PayeeFinancialAccount")
            _cbc(acct, "ID", bank["iban"].replace(" ", ""))
            _cbc(acct, "PaymentNote", number)
            if bank["bic"]:
                branch = _cac(acct, "FinancialInstitutionBranch")
                _cbc(_cac(branch, "FinancialInstitution"), "ID", bank["bic"])
    terms = _cac(root, "PaymentTerms")
    _cbc(terms, "ID", "1")
    if means_id:
        _cbc(terms, "PaymentMeansID", means_id)
    _amount(terms, "Amount", payable, currency)  # F-INV134: = PayableAmount


def _oioubl_document(kind, *, number, issue_date, due_date, currency, note, billing_reference, supplier,
                     customer, lines):
    import uuid as _uuid

    profile = PROFILES["oioubl"]
    invoice = kind == "invoice"
    root = ET.Element(f"{{{NS_INVOICE if invoice else NS_CREDIT_NOTE}}}{'Invoice' if invoice else 'CreditNote'}")
    _cbc(root, "UBLVersionID", profile["ubl_version"])
    _cbc(root, "CustomizationID", profile["customization"])
    _cbc(root, "ProfileID", profile["profile"], schemeAgencyID="320", schemeID=profile["profile_scheme"])
    _cbc(root, "ID", number)
    _cbc(root, "CopyIndicator", "false")
    _cbc(root, "UUID", str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"{kind}:{supplier.cvr}:{number}")))
    _cbc(root, "IssueDate", issue_date.isoformat())
    if invoice:
        _cbc(root, "InvoiceTypeCode", "380", listAgencyID="320", listID="urn:oioubl:codelist:invoicetypecode-1.1")
    if note:
        _cbc(root, "Note", note[:1000])
    _cbc(root, "DocumentCurrencyCode", currency)
    if billing_reference:
        ref = _cac(_cac(root, "BillingReference"), "InvoiceDocumentReference")
        _cbc(ref, "ID", billing_reference)
    _oio_party(root, "AccountingSupplierParty", supplier, "1")
    _oio_party(root, "AccountingCustomerParty", customer, "1")
    breakdown = tax_breakdown(lines)
    line_total = money(sum((l.amount for l in lines), Decimal("0")))
    tax_total = money(sum((t for _, t in breakdown.values()), Decimal("0")))
    if invoice:
        _oio_payment(root, number, due_date, currency, line_total + tax_total)
    _oio_tax_total(root, breakdown, currency)
    lmt = _cac(root, "LegalMonetaryTotal")
    _amount(lmt, "LineExtensionAmount", line_total, currency)
    _amount(lmt, "TaxExclusiveAmount", tax_total, currency)   # OIOUBL: momsbeløbet
    _amount(lmt, "TaxInclusiveAmount", line_total + tax_total, currency)
    _amount(lmt, "PayableAmount", line_total + tax_total, currency)
    line_tag, qty_tag = ("InvoiceLine", "InvoicedQuantity") if invoice else ("CreditNoteLine", "CreditedQuantity")
    for i, l in enumerate(lines, start=1):
        el = _cac(root, line_tag)
        _cbc(el, "ID", i)
        _cbc(el, qty_tag, fmt_qty(l.quantity), unitCode="EA")
        _amount(el, "LineExtensionAmount", l.amount, currency)
        _oio_tax_total(el, tax_breakdown([l]), currency)
        item = _cac(el, "Item")
        name = (l.description or "Vare/ydelse")[:200]
        _cbc(item, "Description", name)
        _cbc(item, "Name", name)
        price = _cac(el, "Price")
        _amount(price, "PriceAmount", l.unit_price, currency)
        _cbc(price, "BaseQuantity", "1", unitCode="EA")
        _cbc(price, "OrderableUnitFactorRate", "1")
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def build_invoice(invoice, fmt="peppol"):
    customer = invoice.customer
    return _document(
        "invoice", fmt, number=invoice.invoice_number, issue_date=invoice.date, due_date=invoice.due_date,
        currency=(invoice.currency or "DKK").upper(), note=invoice.notes,
        buyer_reference=getattr(invoice, "buyer_reference", "") or getattr(customer, "code", ""),
        billing_reference=None, supplier=supplier_party(), customer=customer_party(customer),
        lines=invoice_lines(invoice), payment_terms_days=getattr(customer, "payment_terms", None))


def build_credit_note(credit_note, fmt="peppol"):
    customer = credit_note.customer
    invoice = credit_note.invoice
    currency = (getattr(credit_note, "currency", "") or (invoice.currency if invoice else "") or "DKK").upper()
    lines = []
    if hasattr(credit_note, "lines"):
        for l in credit_note.lines.select_related("tax_code").all():
            if getattr(l, "is_text", False):
                continue
            cat, pct = tax_category(l.tax_code)
            lines.append(Line(l.description, Decimal(str(l.quantity)), Decimal(str(l.unit_price)), cat, pct))
    if not lines:
        lines = [_single_line(credit_note.subtotal, credit_note.tax_amount,
                              f"Kreditering af faktura {invoice.invoice_number}" if invoice else "Kreditering")]
    return _document(
        "credit_note", fmt, number=credit_note.credit_note_number, issue_date=credit_note.date, due_date=None,
        currency=currency, note=credit_note.notes,
        buyer_reference=getattr(customer, "code", ""),
        billing_reference=invoice.invoice_number if invoice else None,
        supplier=supplier_party(), customer=customer_party(customer), lines=lines)
