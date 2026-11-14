"""Læsning af indgående UBL (Peppol BIS 3.0, OIOUBL 2.x) og forslag til en regning.

``parse_ubl(xml)`` → dict med afsender, linjer og totaler.
``suggest_bill(parsed)`` → forslag: leverandør (fundet via CVR/GLN), konto og
momskode pr. linje. Forslaget gemmes på IncomingEInvoice og bruges, når en
bruger opretter regningen (``services.to_bill``).

XML'en kommer udefra og læses med defusedxml (ingen entiteter/DTD'er).
"""

import re
from decimal import Decimal, InvalidOperation

from defusedxml import ElementTree as SafeET

from .ubl import NS_CAC, NS_CBC, SCHEME_CVR, SCHEME_GLN, digits


class ParseError(Exception):
    pass


def _local(tag):
    return tag.split("}")[-1]


def _find(el, path):
    """Find med lokale navne: "cac:Party/cbc:Name"."""
    cur = el
    for part in path.split("/"):
        if cur is None:
            return None
        prefix, _, name = part.partition(":")
        ns = {"cac": NS_CAC, "cbc": NS_CBC}[prefix]
        cur = cur.find(f"{{{ns}}}{name}")
    return cur


def _text(el, path, default=""):
    found = _find(el, path)
    return (found.text or "").strip() if found is not None and found.text else default


def _dec(el, path):
    raw = _text(el, path)
    try:
        return Decimal(raw) if raw else Decimal("0")
    except InvalidOperation:
        raise ParseError(f"Ugyldigt tal i {path}: {raw!r}") from None


def _date(el, path):
    from datetime import date

    raw = _text(el, path)
    try:
        return date.fromisoformat(raw[:10]) if raw else None
    except ValueError:
        raise ParseError(f"Ugyldig dato i {path}: {raw!r}") from None


def _iso(d):
    return d.isoformat() if d else None


def _party(root, wrapper):
    party = _find(root, f"cac:{wrapper}/cac:Party")
    if party is None:
        return {}
    endpoint = _find(party, "cbc:EndpointID")
    scheme = (endpoint.get("schemeID") or "") if endpoint is not None else ""
    endpoint_id = (endpoint.text or "").strip() if endpoint is not None and endpoint.text else ""
    # OIOUBL 2.0x brugte schemeID="DK:CVR"/"GLN"
    scheme = {"DK:CVR": SCHEME_CVR, "GLN": SCHEME_GLN, "DK:SE": "DK:SE"}.get(scheme, scheme)
    if scheme == SCHEME_CVR:
        endpoint_id = digits(endpoint_id)  # OIOUBL: "DK12345678"
    vat = _text(party, "cac:PartyTaxScheme/cbc:CompanyID")
    legal = _text(party, "cac:PartyLegalEntity/cbc:CompanyID")
    cvr = ""
    for candidate, is_cvr in ((endpoint_id, scheme == SCHEME_CVR), (legal, True), (vat, vat.upper().startswith("DK"))):
        d = digits(candidate)
        if is_cvr and len(d) == 8:
            cvr = d
            break
    return {
        "name": _text(party, "cac:PartyLegalEntity/cbc:RegistrationName") or _text(party, "cac:PartyName/cbc:Name"),
        "endpoint_scheme": scheme, "endpoint_id": endpoint_id,
        "cvr": cvr, "gln": endpoint_id if scheme == SCHEME_GLN else "", "vat_id": vat,
        "street": _text(party, "cac:PostalAddress/cbc:StreetName"),
        "zip_code": _text(party, "cac:PostalAddress/cbc:PostalZone"),
        "city": _text(party, "cac:PostalAddress/cbc:CityName"),
        "country": _text(party, "cac:PostalAddress/cac:Country/cbc:IdentificationCode"),
        "email": _text(party, "cac:Contact/cbc:ElectronicMail"),
    }


def parse_ubl(xml):
    try:
        root = SafeET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    except Exception as e:  # defusedxml/ParseError
        raise ParseError(f"XML'en kunne ikke læses: {e}") from e
    kind = _local(root.tag)
    if kind not in ("Invoice", "CreditNote"):
        raise ParseError(f"Ukendt dokumenttype: {kind}. Forventede Invoice eller CreditNote.")
    customization = _text(root, "cbc:CustomizationID")
    fmt = "peppol" if "peppol" in customization.lower() else ("oioubl" if "oioubl" in customization.lower() else "")
    line_tag, qty_tag = ("InvoiceLine", "InvoicedQuantity") if kind == "Invoice" else \
        ("CreditNoteLine", "CreditedQuantity")
    lines = []
    for el in root.findall(f"{{{NS_CAC}}}{line_tag}"):
        qty = _dec(el, f"cbc:{qty_tag}")
        amount = _dec(el, "cbc:LineExtensionAmount")
        price = _dec(el, "cac:Price/cbc:PriceAmount")
        base_qty = _dec(el, "cac:Price/cbc:BaseQuantity") or Decimal("1")
        unit_price = price / base_qty if base_qty else price
        if qty and not unit_price:
            unit_price = amount / qty
        lines.append({
            "description": _text(el, "cac:Item/cbc:Name") or _text(el, "cac:Item/cbc:Description"),
            "quantity": str(qty or Decimal("1")),
            "unit_price": str(unit_price.quantize(Decimal("0.01"))),
            "amount": str(amount),
            "tax_category": _text(el, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID"),
            "tax_percent": str(_dec(el, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent")),
        })
    # TaxTotal kan forekomme to gange (dokument- og regnskabsvaluta); den første er dokumentvalutaen.
    tax_total = _dec(root, "cac:TaxTotal/cbc:TaxAmount")
    issue = _date(root, "cbc:IssueDate")
    due = _date(root, "cbc:DueDate") or _date(root, "cac:PaymentMeans/cbc:PaymentDueDate")
    return {
        "document_type": "invoice" if kind == "Invoice" else "credit_note",
        "format": fmt,
        "customization_id": customization,
        "profile_id": _text(root, "cbc:ProfileID"),
        "number": _text(root, "cbc:ID"),
        "issue_date": _iso(issue),
        "due_date": _iso(due),
        "currency": _text(root, "cbc:DocumentCurrencyCode", "DKK").upper(),
        "buyer_reference": _text(root, "cbc:BuyerReference"),
        "billing_reference": _text(root, "cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID"),
        "supplier": _party(root, "AccountingSupplierParty"),
        "customer": _party(root, "AccountingCustomerParty"),
        "lines": lines,
        "line_extension": str(_dec(root, "cac:LegalMonetaryTotal/cbc:LineExtensionAmount")),
        "tax_exclusive": str(_dec(root, "cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount")),
        "tax_total": str(tax_total),
        "tax_inclusive": str(_dec(root, "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount")),
        "payable": str(_dec(root, "cac:LegalMonetaryTotal/cbc:PayableAmount")),
        "payment_iban": _text(root, "cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID"),
        "payment_id": _text(root, "cac:PaymentMeans/cbc:PaymentID"),
    }


def find_supplier(supplier):
    """Leverandør i kundens bøger ud fra CVR (tax_id) eller GLN."""
    from purchases.models import Supplier

    cvr = supplier.get("cvr") or ""
    gln = supplier.get("gln") or ""
    candidates = Supplier.objects.filter(is_active=True)
    for s in candidates.exclude(tax_id=""):
        d = digits(s.tax_id)
        if (cvr and d.endswith(cvr) and len(d) in (8, 10)) or (gln and d == gln):
            return s
    if gln and hasattr(Supplier, "gln"):
        return candidates.filter(gln=gln).first()
    return None


def find_tax_code(percent, category):
    from core.models import TaxCode

    qs = TaxCode.objects.filter(is_active=True, type__in=("purchase", "both"))
    pct = Decimal(str(percent or 0))
    if category == "AE":
        rc = [t for t in qs if re.search(r"omvendt|reverse|\brc\b", f"{t.code} {t.name}", re.I)]
        if rc:
            return rc[0]
    return qs.filter(rate=pct).order_by("-type", "code").first()


def suggest_bill(parsed):
    supplier = find_supplier(parsed.get("supplier") or {})
    account = getattr(supplier, "default_account", None) if supplier else None
    lines = []
    for l in parsed.get("lines", []):
        tc = find_tax_code(l.get("tax_percent"), l.get("tax_category"))
        lines.append({**l, "account_id": str(account.id) if account else None,
                      "account_code": account.code if account else None,
                      "tax_code_id": str(tc.id) if tc else None, "tax_code": tc.code if tc else None})
    return {
        "supplier_id": str(supplier.id) if supplier else None,
        "supplier_name": supplier.name if supplier else (parsed.get("supplier") or {}).get("name", ""),
        "supplier_found": supplier is not None,
        "lines": lines,
    }
