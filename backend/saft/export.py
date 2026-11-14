"""SAF-T Financial DK (Erhvervsstyrelsens danske SAF-T-skema).

``build_saft(date_from, date_to, version="2.1")`` → XML (str).

Skemaerne ligger i saft/xsd/ (hentet fra Erhvervsstyrelsens
git.erst.dk/standard-filformater/standard-filformater, mappen SAF-T/XSD):
  1.0 – Danish_SAF-T_Financial_Schema_v_1_0.xsd
  2.1 – Danish_SAF-T_Financial_Schema_v_2_1.xsd (krav for registrerede
        systemer fra 1. januar 2027)
Begge har targetNamespace urn:StandardAuditFile-Taxation-Financial:DK.
``validate(xml, version)`` validerer mod XSD'en (kræver pakken xmlschema).

Indhold:
  Header          – virksomheden, periode, software
  MasterFiles     – GeneralLedgerAccounts (alle konti, med primo/ultimo),
                    Customers, Suppliers, TaxTable
  GeneralLedgerEntries – Journal → Transaction → Line for alle bogførte
                    posteringer i perioden (kladder er ikke bogført og er ikke med)
Beløb er i DKK (base_debit/base_credit); fremmed valuta står i CurrencyAmount.

SourceDocuments (SalesInvoices med fakturaer og kreditnotaer, PurchaseInvoices og Payments)
dannes i saft/source_documents.py. Manglende oplysninger (fx bankkonti uden IBAN/reg.nr.)
giver advarsler i stats["warnings"] og i Header/HeaderComment.
"""

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.db import connection
from django.db.models import Sum
from django.utils import timezone

NS = "urn:StandardAuditFile-Taxation-Financial:DK"
XSD_DIR = Path(__file__).resolve().parent / "xsd"
XSD = {
    "1.0": XSD_DIR / "Danish_SAF-T_Financial_Schema_v_1_0.xsd",
    "2.1": XSD_DIR / "Danish_SAF-T_Financial_Schema_v_2_1.xsd",
}
SOFTWARE_COMPANY = "Ajan Partners"
SOFTWARE_ID = "Ajan Partners Bogføring"
SOFTWARE_VERSION = "1.0"
ZERO = Decimal("0")
UNKNOWN = "Ikke oplyst"

# journals.Journal.type → SAF-T Journal/Type (2.1: GL, AR, AP, AJ)
JOURNAL_TYPE = {"sales": "AR", "purchases": "AP", "opening": "AJ", "closing": "AJ"}

ACCOUNT_TYPE_MAP = {  # accounts.AccountType.name → SAF-T AccountType
    "asset": "Asset", "assets": "Asset", "aktiv": "Asset", "aktiver": "Asset",
    "liability": "Liability", "liabilities": "Liability", "equity": "Liability", "passiv": "Liability",
    "passiver": "Liability", "egenkapital": "Liability", "gæld": "Liability",
    "revenue": "Sale", "income": "Sale", "indtægt": "Sale", "indtægter": "Sale", "omsætning": "Sale",
    "expense": "Expense", "expenses": "Expense", "omkostning": "Expense", "omkostninger": "Expense",
    "udgift": "Expense", "udgifter": "Expense",
}


def ET_ns(tag):
    return f"{{{NS}}}{tag}"


def _el(parent, tag, text=None):
    el = ET.SubElement(parent, ET_ns(tag))
    if text is not None:
        el.text = str(text)
    return el


def _money(value):
    return f"{Decimal(value or 0).quantize(Decimal('0.01')):.2f}"


def _digits(value):
    return re.sub(r"\D", "", str(value or ""))


def _cvr(value):
    d = _digits(value)
    return d if len(d) == 8 and int(d) >= 10000000 else ""


def _text(value, limit, default=UNKNOWN):
    value = (str(value or "")).strip()
    return value[:limit] if value else default


def split_street(text):
    """"Testvej 12 st. tv\n2100 København Ø" → (gade, nr., postnr., by)."""
    lines = [l.strip() for l in re.split(r"[\n,]", text or "") if l.strip()]
    street = number = zip_code = city = ""
    for line in lines:
        m = re.match(r"^(?:DK-?)?(\d{4})\s+(.+)$", line)
        if m and not zip_code:
            zip_code, city = m.group(1), m.group(2)
            continue
        if not street:
            m = re.match(r"^(.*?)\s+(\d+\S*(?:\s.*)?)$", line)
            street, number = (m.group(1), m.group(2)) if m else (line, "")
    return street, number, zip_code, city


def _address(parent, street, number, city, zip_code, country="DK"):
    a = _el(parent, "Address")
    _el(a, "StreetName", _text(street, 70))
    _el(a, "Number", _text(number, 18, "-"))
    _el(a, "City", _text(city, 35))
    _el(a, "PostalCode", _text(zip_code, 18, "-"))
    _el(a, "Country", (country or "DK")[:2].upper())
    return a


def _balance(parent, prefix, amount):
    """Saldo som enten Debit- eller CreditBalance (xs:choice)."""
    if amount >= 0:
        _el(parent, f"{prefix}DebitBalance", _money(amount))
    else:
        _el(parent, f"{prefix}CreditBalance", _money(-amount))


def _amount(parent, tag, amount, currency, currency_amount, rate):
    a = _el(parent, tag)
    _el(a, "Amount", _money(amount))
    _el(a, "CurrencyCode", currency)
    _el(a, "CurrencyAmount", _money(currency_amount))
    if rate is not None:
        _el(a, "ExchangeRate", f"{Decimal(rate):f}")
    return a


def _account_type(account):
    name = (getattr(account.account_type, "name", "") or "").strip().lower()
    return ACCOUNT_TYPE_MAP.get(name, "Other")


# --- Data -------------------------------------------------------------------

def _posted_lines():
    from journals.models import JournalEntryLine
    return JournalEntryLine.objects.filter(journal_entry__is_posted=True)


def _sums(qs, key):
    out = defaultdict(lambda: ZERO)
    for row in qs.values(key).annotate(d=Sum("base_debit"), c=Sum("base_credit")):
        out[row[key]] = (row["d"] or ZERO) - (row["c"] or ZERO)
    return out


def _company():
    from core.models import CompanySettings

    cs = CompanySettings.objects.first()
    tenant = getattr(connection, "tenant", None)
    street, number, zip_code, city = split_street(getattr(tenant, "address", "") or getattr(cs, "address", ""))
    return {
        "name": getattr(cs, "company_name", "") or getattr(tenant, "name", ""),
        "cvr": _cvr(getattr(tenant, "cvr", "") or getattr(cs, "tax_id", "")),
        "street": street, "number": number,
        "zip": getattr(tenant, "zip_code", "") or zip_code,
        "city": getattr(tenant, "city", "") or getattr(cs, "city", "") or city,
        "email": getattr(cs, "email", "") or getattr(tenant, "email", ""),
        "phone": getattr(cs, "phone", "") or getattr(tenant, "phone", ""),
        "currency": "DKK",
        "iban": getattr(cs, "iban", "") or "", "bank_account_no": getattr(cs, "bank_account_no", "") or "",
        "bank_reg_no": getattr(cs, "bank_reg_no", "") or "",
        "vat_registered": getattr(tenant, "vat_period", "quarter") != "none",
    }


def _contact_person():
    """Kundens administrator (ClientMembership) som kontaktperson, ellers 'Ikke oplyst'."""
    tenant = getattr(connection, "tenant", None)
    try:
        from tenancy.models import ClientMembership
        m = (ClientMembership.objects.select_related("user")
             .filter(client_id=getattr(tenant, "pk", None), role="admin", is_active=True).first())
    except Exception:  # pragma: no cover - fx uden public-skemaet i søgestien
        m = None
    if m and (m.user.first_name or m.user.last_name):
        return m.user.first_name or UNKNOWN, m.user.last_name or UNKNOWN
    return UNKNOWN, UNKNOWN


# --- Opbygning -----------------------------------------------------------------

def _header(root, version, company, date_from, date_to, user, warnings):
    h = _el(root, "Header")
    _el(h, "AuditFileVersion", version)
    _el(h, "AuditFileCountry", "DK")
    _el(h, "AuditFileDateCreated", timezone.localdate().isoformat())
    _el(h, "SoftwareCompanyName", SOFTWARE_COMPANY)
    _el(h, "SoftwareID", SOFTWARE_ID)
    _el(h, "SoftwareVersion", SOFTWARE_VERSION)
    c = _el(h, "Company")
    if version == "2.1":
        _el(c, "CVR", company["cvr"] or "10000000")
    else:
        _el(c, "RegistrationNumber", company["cvr"] or "10000000")
    _el(c, "Name", _text(company["name"], 70))
    _address(c, company["street"], company["number"], company["city"], company["zip"])
    contact = _el(c, "Contact")
    person = _el(contact, "ContactPerson")
    first, last = _contact_person()
    _el(person, "FirstName", _text(first, 35))
    _el(person, "LastName", _text(last, 35))
    if company["phone"]:
        _el(contact, "Telephone", company["phone"][:18])
    if company["email"]:
        _el(contact, "Email", company["email"][:70])
    if company["cvr"] and company["vat_registered"]:
        tr = _el(c, "TaxRegistration")
        _el(tr, "TaxRegistrationNumber", f"DK{company['cvr']}")
        _el(tr, "TaxType", "VAT")
        _el(tr, "TaxAuthority", "Skattestyrelsen")
        _el(tr, "Country", "DK")
    for bank in _bank_accounts(company, warnings):
        b = _el(c, "BankAccount")
        if bank.get("iban"):
            _el(b, "IBANNumber", bank["iban"])
        else:
            _el(b, "BankAccountNumber", _text(bank.get("number"), 35))
            if bank.get("name"):
                _el(b, "BankAccountName", bank["name"][:70])
            _el(b, "SortCode", _text(bank.get("sort_code"), 18))  # reg.nr. (krævet i 2.1)
        _el(b, "CurrencyCode", bank.get("currency") or "DKK")
        if bank.get("account_id"):
            _el(b, "AccountID", bank["account_id"])
    _el(h, "DefaultCurrencyCode", company["currency"])
    sel = _el(h, "SelectionCriteria")
    _el(sel, "SelectionStartDate", date_from.isoformat())
    _el(sel, "SelectionEndDate", date_to.isoformat())
    _el(h, "TaxAccountingBasis", "Regnskabsdata")
    _el(h, "TaxEntity", _text(company["name"], 70))
    if user is not None and getattr(user, "username", ""):
        _el(h, "UserID", user.username[:35])


MISSING = "MANGLER"


def _bank_accounts(company, warnings):
    """Bankkonti til Header (2.1 kræver mindst én).

    Kilder i rækkefølge: CompanySettings (IBAN eller reg.nr./kontonr., bruges på den første
    bankkonto), felter på kontoen eller journalen (iban, bank_reg_no, bank_account_no, hvis
    de findes) og IBAN fra bankkoblingen (integrations.BankFeedConnection). Mangler alt,
    skrives "MANGLER", og der gives en advarsel – der gættes ikke.
    """
    from journals.models import Journal

    feeds = {}
    try:
        from integrations.models import BankFeedConnection
        tenant = getattr(connection, "tenant", None)
        for c in BankFeedConnection.objects.filter(client_id=getattr(tenant, "pk", None)).exclude(iban=""):
            feeds.setdefault(str(c.bank_account_id), c.iban)
    except Exception:  # pragma: no cover - public-skemaet ikke i søgestien
        pass
    out = []
    company_bank = {"iban": (company["iban"] or "").replace(" ", ""), "number": company["bank_account_no"],
                    "sort_code": company["bank_reg_no"]}
    for j in Journal.objects.filter(type="bank").select_related("account").order_by("code"):
        a = j.account
        if a is None:
            continue
        iban = (getattr(a, "iban", "") or getattr(j, "iban", "") or feeds.get(str(a.id), "")).replace(" ", "")
        bank = {"iban": iban, "number": getattr(a, "bank_account_no", "") or getattr(j, "bank_account_no", ""),
                "sort_code": getattr(a, "bank_reg_no", "") or getattr(j, "bank_reg_no", ""),
                "name": j.name, "currency": (j.currency or a.currency or "DKK")[:3], "account_id": a.code}
        if not out and (company_bank["iban"] or company_bank["number"]) and not (bank["iban"] or bank["number"]):
            bank.update({k: v for k, v in company_bank.items() if v})
        out.append(bank)
    if not out and (company_bank["iban"] or company_bank["number"]):
        out.append({**company_bank, "currency": "DKK"})
    if not out:
        out.append({"number": MISSING, "sort_code": MISSING, "currency": "DKK"})
        warnings.append("Ingen bankkonti: opret en bankjournal og udfyld IBAN eller reg.nr./kontonr. i "
                        "Indstillinger. Header/BankAccount er udfyldt med \"MANGLER\".")
    for b in out:
        if not b.get("iban") and not (b.get("number") and b.get("number") != MISSING):
            label = f"{b.get('account_id', '')} {b.get('name', '')}".strip() or "bankkonto"
            if b.get("number") != MISSING:
                warnings.append(f"Bankkonto {label}: IBAN eller reg.nr./kontonr. mangler (udfyld i Indstillinger "
                                f"eller kobl banken på). Skrevet som \"MANGLER\".")
            b["number"] = MISSING
            b["sort_code"] = b.get("sort_code") or MISSING
        elif not b.get("iban") and not b.get("sort_code"):
            warnings.append(f"Bankkonto {b.get('account_id', '')}: reg.nr. mangler. Skrevet som \"MANGLER\".")
            b["sort_code"] = MISSING
    return out


def _gl_accounts(mf, date_from, date_to, version="2.1"):
    from accounts.models import Account

    lines = _posted_lines()
    opening = _sums(lines.filter(journal_entry__date__lt=date_from), "account_id")
    movement = _sums(lines.filter(journal_entry__date__gte=date_from, journal_entry__date__lte=date_to),
                     "account_id")
    gla = _el(mf, "GeneralLedgerAccounts")
    accounts = list(Account.objects.select_related("account_type").order_by("code"))
    if version == "2.1" or any(getattr(a, "standard_code", "") for a in accounts):  # påkrævet i 2.1
        _el(gla, "NameOfStandardAccount", "Standardkontoplanen")
        from integrations.base import setting
        _el(gla, "VersionOfStandardAccount", setting("SAFT_STANDARD_ACCOUNT_VERSION", "20260101"))
    codes = set()
    for a in accounts:
        el = _el(gla, "Account")
        _el(el, "AccountID", a.code)
        _el(el, "AccountDescription", _text(a.name, 256))
        std = getattr(a, "standard_code", "") or ""
        if std:
            _el(el, "StandardAccountID", str(std)[:35])
        _el(el, "AccountType", _account_type(a))
        o = opening[a.id]
        _balance(el, "Opening", o)
        _balance(el, "Closing", o + movement[a.id])
        codes.add(a.code)
    if not accounts:  # GeneralLedgerAccounts kræver mindst én konto
        mf.remove(gla)
    return codes


def _partner_balances(partner_type, ids, date_from, date_to):
    lines = _posted_lines().filter(partner_type=partner_type, partner_id__in=ids)
    return (_sums(lines.filter(journal_entry__date__lt=date_from), "partner_id"),
            _sums(lines.filter(journal_entry__date__gte=date_from, journal_entry__date__lte=date_to),
                  "partner_id"))


def _parties(mf, version, kind, model, account_code, codes, date_from, date_to):
    parties = list(model.objects.order_by("code"))
    if not parties:
        return {}
    keys = [str(p.id) for p in parties] + [p.code for p in parties]
    opening, movement = _partner_balances("customer" if kind == "Customer" else "supplier", keys,
                                          date_from, date_to)
    wrapper = _el(mf, f"{kind}s")
    lookup = {}
    for p in parties:
        el = _el(wrapper, kind)
        cvr = _cvr(p.tax_id)
        if version == "2.1":
            _el(el, f"{kind}ID", p.code)
            _el(el, "CVR" if cvr else "RegistrationNumber", cvr or "10000000")
        elif cvr:
            _el(el, "RegistrationNumber", cvr)
        _el(el, "Name", _text(p.name, 70))
        street, number, zip_code, city = split_street(p.address)
        _address(el, getattr(p, "street", "") or street, number, getattr(p, "city", "") or city,
                 getattr(p, "postal_code", "") or getattr(p, "zip_code", "") or zip_code,
                 getattr(p, "country", "") or "DK")
        if p.tax_id and p.tax_id.strip():
            tr = _el(el, "TaxRegistration")
            tax_id = p.tax_id.strip().replace(" ", "")
            _el(tr, "TaxRegistrationNumber", (f"DK{cvr}" if cvr and not tax_id[:2].isalpha() else tax_id)[:35])
            _el(tr, "TaxType", "VAT")
        if version != "2.1":
            _el(el, f"{kind}ID", p.code)
        if account_code and account_code in codes:
            _el(el, "AccountID", account_code)
        o = opening[str(p.id)] + opening[p.code]
        m = movement[str(p.id)] + movement[p.code]
        _balance(el, "Opening", o)
        _balance(el, "Closing", o + m)
        lookup[str(p.id)] = p.code
        lookup[p.code] = p.code
    return lookup


def _tax_table(mf, version):
    from core.models import TaxCode

    codes = list(TaxCode.objects.order_by("code"))
    if not codes:
        return set()
    tt = _el(mf, "TaxTable")
    entry = _el(tt, "TaxTableEntry")
    _el(entry, "TaxType", "VAT")
    _el(entry, "Description", "VAT" if version == "2.1" else "Moms")  # skemaernes faste værdier
    for t in codes:
        d = _el(entry, "TaxCodeDetails")
        _el(d, "TaxCode", t.code[:9])
        std = getattr(t, "standard_code", "") or getattr(t, "standard_tax_code", "")
        if version == "2.1" and std:
            _el(d, "StandardTaxCode", str(std)[:9])
        _el(d, "EffectiveDate", "2000-01-01")
        _el(d, "Description", _text(t.name, 256))
        _el(d, "TaxPercentage", f"{Decimal(t.rate or 0):f}")
        _el(d, "Country", "DK")
    return {t.code[:9] for t in codes}


def _gl_entries(root, codes, customers, suppliers, date_from, date_to):
    from journals.models import Journal, JournalEntry, JournalEntryLine

    entries = (JournalEntry.objects.filter(is_posted=True, date__gte=date_from, date__lte=date_to)
               .select_related("journal").order_by("journal__code", "date", "entry_number"))
    line_qs = (JournalEntryLine.objects.filter(journal_entry__in=entries).select_related("account")
               .order_by("journal_entry_id", "line_no", "id"))
    by_entry = defaultdict(list)
    for l in line_qs:
        by_entry[l.journal_entry_id].append(l)
    total_d = total_c = ZERO
    gle = _el(root, "GeneralLedgerEntries")
    n_el = _el(gle, "NumberOfEntries")
    d_el = _el(gle, "TotalDebit")
    c_el = _el(gle, "TotalCredit")
    count = 0
    tx = {}
    journals = {j.id: j for j in Journal.objects.all()}
    current = None
    j_el = None
    for e in entries:
        lines = by_entry.get(e.id) or []
        if not lines:
            continue
        if e.journal_id != current:
            current = e.journal_id
            j = journals[e.journal_id]
            j_el = _el(gle, "Journal")
            _el(j_el, "JournalID", j.code[:18])
            _el(j_el, "Description", _text(j.name, 256))
            _el(j_el, "Type", JOURNAL_TYPE.get(j.type, "GL"))
        t = _el(j_el, "Transaction")
        _el(t, "TransactionID", e.entry_number[:70])
        tx[e.id] = e.entry_number[:70]
        _el(t, "Period", e.date.month)
        _el(t, "PeriodYear", e.date.year)
        _el(t, "TransactionDate", e.date.isoformat())
        if e.piece_number:
            _el(t, "SourceID", e.piece_number[:35])
        if e.source:
            _el(t, "TransactionType", e.source[:18])
        _el(t, "Description", _text(e.description or e.reference, 256, e.entry_number))
        _el(t, "SystemEntryDate", timezone.localtime(e.created_at).date().isoformat()
            if e.created_at else e.date.isoformat())
        _el(t, "GLPostingDate", (timezone.localtime(e.validated_at).date() if e.validated_at else e.date).isoformat())
        _el(t, "SystemID", str(e.entry_number)[:18])
        count += 1
        for i, l in enumerate(lines, start=1):
            le = _el(t, "Line")
            _el(le, "RecordID", str(l.line_no or i)[:18])
            _el(le, "AccountID", l.account.code)
            if l.partner_type == "customer" and l.partner_id in customers:
                _el(le, "CustomerID", customers[l.partner_id])
            elif l.partner_type == "supplier" and l.partner_id in suppliers:
                _el(le, "SupplierID", suppliers[l.partner_id])
            _el(le, "Description", _text(l.description or e.description, 256, e.entry_number))
            currency = (l.currency or "DKK").upper()[:3]
            foreign = currency != "DKK"
            if (l.base_debit or ZERO) > 0 or ((l.base_credit or ZERO) == 0):
                amount, cur_amount, tag = l.base_debit or ZERO, l.debit or ZERO, "DebitAmount"
                total_d += amount
            else:
                amount, cur_amount, tag = l.base_credit or ZERO, l.credit or ZERO, "CreditAmount"
                total_c += amount
            _amount(le, tag, amount, currency, cur_amount if foreign else amount,
                    l.exchange_rate if foreign else Decimal("1"))
    n_el.text = str(count)
    d_el.text = _money(total_d)
    c_el.text = _money(total_c)
    return {"entries": count, "total_debit": total_d, "total_credit": total_c, "_tx": tx}


def build_saft(date_from, date_to, version="2.1", user=None):
    """Returnerer (xml, stats)."""
    from accounts import chart
    from purchases.models import Supplier
    from sales.models import Customer

    if version not in XSD:
        raise ValueError(f"Ukendt SAF-T-version {version}. Gyldige: {', '.join(XSD)}")
    if isinstance(date_from, str):
        date_from = date.fromisoformat(date_from)
    if isinstance(date_to, str):
        date_to = date.fromisoformat(date_to)
    if date_to < date_from:
        raise ValueError("Slutdatoen ligger før startdatoen.")
    ET.register_namespace("", NS)
    root = ET.Element(ET_ns("AuditFile"))
    company = _company()
    warnings = []
    _header(root, version, company, date_from, date_to, user, warnings)
    mf = _el(root, "MasterFiles")
    codes = _gl_accounts(mf, date_from, date_to, version)
    customers = _parties(mf, version, "Customer", Customer, getattr(chart, "RECEIVABLE", ""), codes,
                         date_from, date_to)
    suppliers = _parties(mf, version, "Supplier", Supplier, getattr(chart, "PAYABLE", ""), codes,
                         date_from, date_to)
    tax_codes = _tax_table(mf, version)
    if not len(mf):
        root.remove(mf)
    stats = _gl_entries(root, codes, customers, suppliers, date_from, date_to)
    stats["accounts"] = len(codes)
    from . import export as ex
    from .source_documents import SourceDocumentsBuilder
    stats.update(SourceDocumentsBuilder(ex, root, version, codes, customers, suppliers, tax_codes,
                                        stats.pop("_tx"), warnings).build(date_from, date_to))
    stats["warnings"] = warnings
    if warnings:
        header = root.find(ET_ns("Header"))
        idx = list(header).index(header.find(ET_ns("SelectionCriteria"))) + 1
        comment = ET.Element(ET_ns("HeaderComment"))
        comment.text = ("ADVARSEL: " + " | ".join(warnings))[:256]
        header.insert(idx, comment)
    ET.indent(root)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")
    return xml, stats


def validate(xml, version="1.0"):
    """Liste af XSD-fejl (tom = gyldig). Kræver xmlschema."""
    schema = _schema(version)
    return [f"{e.path}: {e.reason}" for e in schema.iter_errors(xml)]


_SCHEMAS = {}


def _schema(version):
    import xmlschema

    if version not in _SCHEMAS:
        _SCHEMAS[version] = xmlschema.XMLSchema(str(XSD[version]))
    return _SCHEMAS[version]

