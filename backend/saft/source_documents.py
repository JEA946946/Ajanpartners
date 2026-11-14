"""SAF-T SourceDocuments: SalesInvoices, PurchaseInvoices og Payments.

Et kildedokument tages kun med, når dets postering er bogført og ligger i
GeneralLedgerEntries i samme fil. Skemaet kræver, at ``TransactionID`` på
fakturaen eller betalingen henviser til en Transaction i filen
(keyref ``KeyTransactionReference``).

Beløb er i DKK (Amount). Fremmed valuta står i CurrencyAmount og ExchangeRate.
"""

from collections import OrderedDict
from decimal import Decimal

ZERO = Decimal("0")

# Fast tekst (SAFcodeType, højst 9 tegn)
INVOICE_TYPE = {"invoice": "Faktura", "credit_note": "Kredit", "bill": "Regning"}
GOODS_SERVICES = "Services"
PAYMENT_METHOD = {"bank_transfer": "Bank", "cash": "Kontant", "card": "Kort", "check": "Check"}


def _d(value):
    return Decimal(str(value or 0))


def number_of(doc):
    return getattr(doc, "invoice_number", "") or getattr(doc, "credit_note_number", "") or str(doc)


class SourceDocumentsBuilder:
    """Bygges efter GeneralLedgerEntries. ``tx`` er {journal_entry_id: TransactionID} for
    de posteringer, der er med i filen."""

    def __init__(self, ex, root, version, codes, customers, suppliers, tax_codes, tx, warnings):
        self.ex = ex                # saft.export (hjælpefunktioner)
        self.root = root
        self.version = version
        self.codes = codes
        self.customers = customers  # {id|code: code}
        self.suppliers = suppliers
        self.tax_codes = tax_codes  # TaxCode-koder, der står i TaxTable
        self.tx = tx
        self.warnings = warnings
        self.counts = {"sales_invoices": 0, "purchase_invoices": 0, "payments": 0}

    # --- små hjælpere ----------------------------------------------------
    def el(self, parent, tag, text=None):
        return self.ex._el(parent, tag, text)

    def amount(self, parent, tag, amount_dkk, currency, currency_amount, rate):
        foreign = currency != "DKK"
        return self.ex._amount(parent, tag, amount_dkk, currency, currency_amount if foreign else amount_dkk,
                               rate if foreign else Decimal("1"))

    def address(self, parent, tag, party):
        street, number, zip_code, city = self.ex.split_street(getattr(party, "address", ""))
        a = self.el(parent, tag)
        self.el(a, "StreetName", self.ex._text(street, 70))
        self.el(a, "Number", self.ex._text(number, 18, "-"))
        self.el(a, "City", self.ex._text(getattr(party, "city", "") or city, 35))
        self.el(a, "PostalCode", self.ex._text(getattr(party, "postal_code", "") or zip_code, 18, "-"))
        self.el(a, "Country", (getattr(party, "country", "") or "DK")[:2].upper())

    def tax_info(self, parent, tag, tax_code, base_dkk, tax_dkk, currency, rate, base_cur, tax_cur):
        t = self.el(parent, tag)
        self.el(t, "TaxType", "VAT")
        if tax_code is not None and tax_code.code[:9] in self.tax_codes:
            self.el(t, "TaxCode", tax_code.code[:9])
            std = getattr(tax_code, "standard_code", "")
            if self.version == "2.1" and std:
                self.el(t, "StandardTaxCode", str(std)[:9])
            self.el(t, "TaxPercentage", f"{_d(tax_code.rate):f}")
        self.el(t, "TaxBase", self.ex._money(base_dkk))
        self.amount(t, "TaxAmount", tax_dkk, currency, tax_cur, rate)
        return t

    def infer_tax_code(self, subtotal, tax_amount, types):
        """Momskoden for et dokument uden linjer: satsen = moms / grundlag."""
        from core.models import TaxCode

        subtotal, tax_amount = _d(subtotal), _d(tax_amount)
        rate = (tax_amount / subtotal * 100).quantize(Decimal("1")) if subtotal else ZERO
        for t in TaxCode.objects.filter(rate=rate, type__in=types).order_by("code"):
            if t.code[:9] in self.tax_codes:
                return t
        return None

    def entry_ok(self, entry_id):
        return entry_id is not None and entry_id in self.tx

    def entry_account(self, entry_id, side, exclude=()):
        """Første konto på posteringen med beløb på siden (debit/credit), som ikke er udelukket."""
        from journals.models import JournalEntryLine

        field = "base_debit" if side == "debit" else "base_credit"
        for l in (JournalEntryLine.objects.filter(journal_entry_id=entry_id, **{f"{field}__gt": 0})
                  .select_related("account").order_by("line_no")):
            if l.account.code in self.codes and l.account.code not in exclude:
                return l.account.code
        return None

    def section(self, tag):
        sd = self.root.find(self.ex.ET_ns("SourceDocuments"))
        if sd is None:
            sd = self.el(self.root, "SourceDocuments")
        sec = self.el(sd, tag)
        return sec, self.el(sec, "NumberOfEntries"), self.el(sec, "TotalDebit"), self.el(sec, "TotalCredit")

    # --- fakturaer ---------------------------------------------------------
    def _invoice(self, sec, *, number, party_tag, party_id, party, account_id, date, kind, entry_id,
                 lines, currency, rate, payment_terms=None, source_id=None):
        """lines: [(account_code, description, qty, unit_price_cur, amount_cur, tax_code, indicator)]"""
        inv = self.el(sec, "Invoice")
        self.el(inv, "InvoiceNo", number[:70])
        info = self.el(inv, party_tag)
        # xs:choice: ID (henviser til MasterFiles) eller Name – ID'en bruges
        self.el(info, "CustomerID" if party_tag == "CustomerInfo" else "SupplierID", party_id)
        self.address(info, "BillingAddress", party)
        if account_id:
            self.el(inv, "AccountID", account_id)
        self.el(inv, "Period", date.month)
        self.el(inv, "PeriodYear", date.year)
        self.el(inv, "InvoiceDate", date.isoformat())
        self.el(inv, "InvoiceType", INVOICE_TYPE[kind])
        if payment_terms:
            self.el(inv, "PaymentTerms", str(payment_terms)[:70])
        if source_id:
            self.el(inv, "SourceID", str(source_id)[:35])
        self.el(inv, "GLPostingDate", date.isoformat())
        self.el(inv, "TransactionID", self.tx[entry_id])
        totals = OrderedDict()
        debit = credit = net = ZERO
        for i, (acct, text, qty, price_cur, amount_cur, tax_code, ind) in enumerate(lines, start=1):
            ln = self.el(inv, "Line")
            self.el(ln, "LineNumber", str(i))
            self.el(ln, "AccountID", acct)
            self.el(ln, "GoodsServicesID", GOODS_SERVICES)
            self.el(ln, "Quantity", f"{_d(qty):f}")
            self.el(ln, "UnitPrice", self.ex._money(_d(price_cur) * rate))
            self.el(ln, "InvoiceDate", date.isoformat())
            self.el(ln, "Description", self.ex._text(text, 256, number))
            amount_dkk = (_d(amount_cur) * rate).quantize(Decimal("0.01"))
            self.amount(ln, "InvoiceLineAmount", amount_dkk, currency, amount_cur, rate)
            self.el(ln, "DebitCreditIndicator", ind)
            tax_pct = _d(getattr(tax_code, "rate", 0))
            tax_cur = (_d(amount_cur) * tax_pct / 100).quantize(Decimal("0.01"))
            tax_dkk = (tax_cur * rate).quantize(Decimal("0.01"))
            if tax_code is not None:
                self.tax_info(ln, "TaxInformation", tax_code, amount_dkk, tax_dkk, currency, rate, amount_cur, tax_cur)
            key = tax_code.code if tax_code is not None else ""
            b, t, bc, tc, obj = totals.get(key, (ZERO, ZERO, ZERO, ZERO, tax_code))
            totals[key] = (b + amount_dkk, t + tax_dkk, bc + _d(amount_cur), tc + tax_cur, obj)
            net += amount_dkk
            if ind in ("D", "Debit"):
                debit += amount_dkk
            else:
                credit += amount_dkk
        dt = self.el(inv, "DocumentTotals")
        gross = net
        if not totals:
            totals[""] = (ZERO, ZERO, ZERO, ZERO, None)
        for base, tax, base_cur, tax_cur, obj in totals.values():
            self.tax_info(dt, "TaxInformationTotals", obj, base, tax, currency, rate, base_cur, tax_cur)
            gross += tax
        self.el(dt, "NetTotal", self.ex._money(net))
        self.el(dt, "GrossTotal", self.ex._money(gross))
        return debit, credit

    def sales_invoices(self, date_from, date_to):
        from accounts import chart
        from sales.models import CreditNote, Invoice

        receivable = getattr(chart, "RECEIVABLE", "")
        docs = []
        for inv in (Invoice.objects.filter(date__gte=date_from, date__lte=date_to, journal_entry__isnull=False)
                    .select_related("customer").prefetch_related("lines__account", "lines__tax_code")
                    .order_by("date", "invoice_number")):
            if self.entry_ok(inv.journal_entry_id):
                docs.append(("invoice", inv))
        for cn in (CreditNote.objects.filter(date__gte=date_from, date__lte=date_to, journal_entry__isnull=False)
                   .select_related("customer", "invoice").order_by("date", "credit_note_number")):
            if self.entry_ok(cn.journal_entry_id):
                docs.append(("credit_note", cn))
        if not docs:
            return
        sec, n_el, d_el, c_el = self.section("SalesInvoices")
        td = tc = ZERO
        for kind, doc in docs:
            customer = doc.customer
            cid = self.customers.get(str(customer.id)) or self.customers.get(customer.code)
            if not cid:
                self.warnings.append(f"Faktura {getattr(doc, 'invoice_number', getattr(doc, 'credit_note_number', ''))}: "
                                     "kunden mangler i debitorlisten og er udeladt af SourceDocuments.")
                continue
            header_acct = self.entry_account(doc.journal_entry_id, "debit" if kind == "invoice" else "credit")
            if receivable in self.codes and header_acct is None:
                header_acct = receivable
            fallback = self.entry_account(doc.journal_entry_id, "credit" if kind == "invoice" else "debit",
                                          exclude=(receivable,)) or header_acct
            ind = "C" if kind == "invoice" else "D"
            currency = (getattr(doc, "currency", "") or getattr(getattr(doc, "invoice", None), "currency", "")
                        or "DKK").upper()[:3]
            rate = _d(getattr(doc, "exchange_rate", None) or getattr(getattr(doc, "invoice", None), "exchange_rate",
                                                                      None) or 1) if currency != "DKK" else Decimal("1")
            lines = []
            if kind == "invoice":
                for l in doc.lines.all():
                    if l.is_text:
                        continue
                    acct = l.account.code if l.account_id and l.account.code in self.codes else fallback
                    if acct:
                        lines.append((acct, l.description, l.quantity, l.unit_price, l.amount, l.tax_code, ind))
            if not lines and fallback:
                text = (f"Kreditering af faktura {doc.invoice.invoice_number}" if kind == "credit_note" and doc.invoice
                        else (doc.notes or "Faktura"))
                code = self.infer_tax_code(doc.subtotal, doc.tax_amount, ("sales", "both"))
                if code is None:
                    self.warnings.append(f"{number_of(doc)}: momskoden kunne ikke bestemmes.")
                lines.append((fallback, text, 1, doc.subtotal, doc.subtotal, code, ind))
            if not lines:
                self.warnings.append(f"Dokument {doc}: ingen konto til linjerne – udeladt af SourceDocuments.")
                continue
            number = doc.invoice_number if kind == "invoice" else doc.credit_note_number
            d, c = self._invoice(sec, number=number, party_tag="CustomerInfo", party_id=cid, party=customer,
                                 account_id=header_acct, date=doc.date, kind=kind, entry_id=doc.journal_entry_id,
                                 lines=lines, currency=currency, rate=rate,
                                 payment_terms=getattr(doc, "payment_terms_code", "") or None)
            td, tc = td + d, tc + c
            self.counts["sales_invoices"] += 1
        self._close(sec, n_el, d_el, c_el, "Invoice", td, tc)

    def purchase_invoices(self, date_from, date_to):
        from accounts import chart
        from purchases.models import Bill

        payable = getattr(chart, "PAYABLE", "")
        bills = [b for b in (Bill.objects.filter(date__gte=date_from, date__lte=date_to, journal_entry__isnull=False)
                             .select_related("supplier").prefetch_related("lines__account", "lines__tax_code")
                             .order_by("date", "bill_number"))
                 if self.entry_ok(b.journal_entry_id)]
        if not bills:
            return
        sec, n_el, d_el, c_el = self.section("PurchaseInvoices")
        td = tc = ZERO
        for bill in bills:
            sid = (self.suppliers.get(str(bill.supplier_id)) or self.suppliers.get(bill.supplier.code)) \
                if bill.supplier_id else None
            if not sid:
                self.warnings.append(f"Regning {bill.bill_number}: mangler leverandør – udeladt af SourceDocuments.")
                continue
            header_acct = self.entry_account(bill.journal_entry_id, "credit")
            if payable in self.codes and header_acct is None:
                header_acct = payable
            fallback = self.entry_account(bill.journal_entry_id, "debit", exclude=(payable,)) or header_acct
            currency = (bill.currency or "DKK").upper()[:3]
            rate = _d(bill.exchange_rate or 1) if currency != "DKK" else Decimal("1")
            lines = []
            for l in bill.lines.all():
                acct = l.account.code if l.account_id and l.account.code in self.codes else fallback
                if acct:
                    lines.append((acct, l.description, l.quantity, l.unit_price, l.amount, l.tax_code, "D"))
            if not lines and fallback:
                code = self.infer_tax_code(bill.subtotal, bill.tax_amount, ("purchase", "both"))
                lines.append((fallback, bill.notes or "Regning", 1, bill.subtotal, bill.subtotal, code, "D"))
            if not lines:
                self.warnings.append(f"Regning {bill.bill_number}: ingen konto til linjerne – udeladt.")
                continue
            d, c = self._invoice(sec, number=bill.reference or bill.bill_number, party_tag="SupplierInfo",
                                 party_id=sid, party=bill.supplier, account_id=header_acct, date=bill.date,
                                 kind="bill", entry_id=bill.journal_entry_id, lines=lines, currency=currency,
                                 rate=rate, source_id=bill.bill_number)
            td, tc = td + d, tc + c
            self.counts["purchase_invoices"] += 1
        self._close(sec, n_el, d_el, c_el, "Invoice", td, tc)

    def payments(self, date_from, date_to):
        from core.models import Payment
        from journals.models import JournalEntryLine

        payments = [p for p in (Payment.objects.filter(date__gte=date_from, date__lte=date_to,
                                                       journal_entry__isnull=False)
                                .select_related("customer", "supplier").order_by("date", "payment_number"))
                    if self.entry_ok(p.journal_entry_id)]
        if not payments:
            return
        sec, n_el, d_el, c_el = self.section("Payments")
        td = tc = ZERO
        for p in payments:
            pay = self.el(sec, "Payment")
            self.el(pay, "PaymentRefNo", p.payment_number[:35])
            self.el(pay, "Period", p.date.month)
            self.el(pay, "PeriodYear", p.date.year)
            self.el(pay, "TransactionID", self.tx[p.journal_entry_id])
            self.el(pay, "TransactionDate", p.date.isoformat())
            self.el(pay, "PaymentMethod", PAYMENT_METHOD.get(p.method, (p.method or "Bank")[:9]))
            self.el(pay, "Description", self.ex._text(p.notes or p.reference, 256, p.payment_number))
            gross = ZERO
            for i, l in enumerate(JournalEntryLine.objects.filter(journal_entry_id=p.journal_entry_id)
                                  .select_related("account").order_by("line_no"), start=1):
                ln = self.el(pay, "Line")
                self.el(ln, "LineNumber", str(i))
                if l.account.code in self.codes:
                    self.el(ln, "AccountID", l.account.code)
                if l.partner_type == "customer" and l.partner_id in self.customers:
                    self.el(ln, "CustomerID", self.customers[l.partner_id])
                elif l.partner_type == "supplier" and l.partner_id in self.suppliers:
                    self.el(ln, "SupplierID", self.suppliers[l.partner_id])
                self.el(ln, "Description", self.ex._text(l.description or p.reference, 256, p.payment_number))
                is_debit = _d(l.base_debit) > 0
                amount = _d(l.base_debit) if is_debit else _d(l.base_credit)
                currency = (l.currency or "DKK").upper()[:3]
                # Payments/Line: 1.0 bruger D/C, 2.1 bruger Debit/Credit (fakturalinjer er D/C i begge)
                if self.version == "2.1":
                    self.el(ln, "DebitCreditIndicator", "Debit" if is_debit else "Credit")
                else:
                    self.el(ln, "DebitCreditIndicator", "D" if is_debit else "C")
                self.amount(ln, "PaymentLineAmount", amount, currency, _d(l.debit) if is_debit else _d(l.credit),
                            _d(l.exchange_rate or 1))
                if is_debit:
                    td += amount
                    gross += amount
                else:
                    tc += amount
            dt = self.el(pay, "DocumentTotals")
            self.el(dt, "GrossTotal", self.ex._money(gross))
            self.counts["payments"] += 1
        self._close(sec, n_el, d_el, c_el, "Payment", td, tc)

    def _close(self, sec, n_el, d_el, c_el, child, td, tc):
        n = len(sec.findall(self.ex.ET_ns(child)))
        if n == 0:
            parent = self.root.find(self.ex.ET_ns("SourceDocuments"))
            parent.remove(sec)
            if not len(parent):
                self.root.remove(parent)
            return
        n_el.text = str(n)
        d_el.text = self.ex._money(td)
        c_el.text = self.ex._money(tc)

    def build(self, date_from, date_to):
        self.sales_invoices(date_from, date_to)
        self.purchase_invoices(date_from, date_to)
        self.payments(date_from, date_to)
        return self.counts
