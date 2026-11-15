"""Læs en leverandørfaktura (PDF eller XML) lokalt og foreslå en regning.

Intet sendes til eksterne tjenester. Rækkefølge:
  1. XML (OIOUBL/Peppol) – præcis aflæsning via einvoice.parse.
  2. PDF med en indlejret OIOUBL/Peppol-fil (fx fra e-conomic, Dinero, Billy) – præcis.
  3. PDF med tekst – danske fakturamønstre: CVR, fakturanr., datoer, beløb, moms og linjer.
     Hvert felt får en sikkerhed (high/medium/low), og beløbene afstemmes
     (netto + moms = total, moms ≈ 25 % af netto).
  4. Scannede PDF'er og billeder har ingen tekst. De kan kun læses, hvis Tesseract
     (lokal OCR) er installeret på serveren; ellers forklares det, og bilaget gemmes.

Resultatet er altid et forslag til en kladde. En bruger tjekker og godkender.
"""

import io
import re
import shutil
from datetime import date
from decimal import Decimal, InvalidOperation

TWO = Decimal("0.01")
MONTHS = {"januar": 1, "februar": 2, "marts": 3, "april": 4, "maj": 5, "juni": 6, "juli": 7, "august": 8,
          "september": 9, "oktober": 10, "november": 11, "december": 12,
          "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "okt": 10,
          "nov": 11, "dec": 12}

AMOUNT = r"-?\d{1,3}(?:[.\s]\d{3})*,\d{2}|-?\d+,\d{2}|-?\d{1,3}(?:,\d{3})*\.\d{2}"
DATE = (r"\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}|\d{4}-\d{2}-\d{2}"
        r"|\d{1,2}\.?\s+(?:januar|februar|marts|april|maj|juni|juli|august|september|oktober|november|december"
        r"|jan|feb|mar|apr|jun|jul|aug|sep|okt|nov|dec)\.?\s+\d{4}")


class ReadError(Exception):
    pass


# ─── Indgang ──────────────────────────────────────────────────────────────────

def read_invoice(content, filename="", own_cvr=""):
    """Returnerer {"source", "parsed", "confidence", "warnings", "text"}.
    ``parsed`` har samme form som einvoice.parse.parse_ubl, så forslaget til regningen
    (leverandør, konto, momskode) laves på samme måde for alle kilder."""
    name = (filename or "").lower()
    head = content[:1024].lstrip()
    if name.endswith(".xml") or head.startswith(b"<?xml") or head.startswith(b"<Invoice"):
        return _from_xml(content, "xml")
    if name.endswith(".pdf") or head.startswith(b"%PDF"):
        embedded = _embedded_xml(content)
        if embedded:
            try:
                return _from_xml(embedded, "pdf_embedded_xml")
            except ReadError:
                pass
        text = _pdf_text(content)
        if len(text.strip()) < 40:
            text = _ocr_pdf(content)
            if text is None:
                raise ReadError("PDF'en er en scanning uden tekst. Den kan ikke læses lokalt, fordi OCR "
                                "(Tesseract) ikke er installeret på serveren. Bilaget er gemt – udfyld "
                                "regningen manuelt.")
            return _from_text(text, own_cvr, "pdf_ocr")
        return _from_text(text, own_cvr, "pdf_text")
    if name.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic")):
        text = _ocr_image(content)
        if text is None:
            raise ReadError("Billeder kan kun læses lokalt med OCR (Tesseract), som ikke er installeret på "
                            "serveren. Bilaget er gemt – udfyld regningen manuelt.")
        return _from_text(text, own_cvr, "image_ocr")
    raise ReadError("Kun PDF og XML (OIOUBL/Peppol) kan læses. Bilaget er gemt.")


# ─── XML ──────────────────────────────────────────────────────────────────────

def _from_xml(content, source):
    from einvoice.parse import ParseError, parse_ubl
    try:
        parsed = parse_ubl(content)
    except ParseError as e:
        raise ReadError(str(e)) from e
    conf = {k: "high" for k in ("supplier", "number", "issue_date", "due_date", "lines", "totals")}
    return {"source": source, "parsed": parsed, "confidence": conf, "warnings": [], "text": ""}


def _embedded_xml(content):
    """Første indlejrede XML-fil i PDF'en, der ligner en UBL-faktura."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            doc = pdf.doc
            names = doc.catalog.get("Names")
            names = names.resolve() if hasattr(names, "resolve") else names
            if not names or "EmbeddedFiles" not in names:
                return None
            from pdfminer.pdftypes import resolve1
            tree = resolve1(names["EmbeddedFiles"])
            pairs = list(resolve1(tree.get("Names", [])) or [])
            for kid in resolve1(tree.get("Kids", [])) or []:
                pairs += list(resolve1(resolve1(kid).get("Names", [])) or [])
            for i in range(1, len(pairs), 2):
                spec = resolve1(pairs[i])
                ef = resolve1(spec.get("EF", {}))
                stream = resolve1(ef.get("F") or ef.get("UF"))
                if stream is None:
                    continue
                data = stream.get_data()
                if b"urn:oasis:names:specification:ubl" in data[:4000]:
                    return data
    except Exception:  # noqa: BLE001 – en defekt PDF skal bare læses som tekst
        return None
    return None


# ─── PDF-tekst og lokal OCR ──────────────────────────────────────────────────

def _pdf_text(content):
    import pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [p.extract_text(x_tolerance=1.5, y_tolerance=3) or "" for p in pdf.pages[:10]]
    except Exception as e:  # noqa: BLE001
        raise ReadError(f"PDF'en kunne ikke åbnes: {e}") from e
    return "\n".join(pages)


def ocr_available():
    if not shutil.which("tesseract"):
        return False
    try:
        import pytesseract  # noqa: F401
        return True
    except ImportError:
        return False


def _ocr_image(content):
    if not ocr_available():
        return None
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(io.BytesIO(content)), lang="dan+eng")


def _ocr_pdf(content):
    if not ocr_available():
        return None
    import pypdfium2
    import pytesseract
    pdf = pypdfium2.PdfDocument(content)
    out = []
    for i in range(min(len(pdf), 5)):
        image = pdf[i].render(scale=2.5).to_pil()
        out.append(pytesseract.image_to_string(image, lang="dan+eng"))
    return "\n".join(out)


# ─── Danske fakturamønstre ───────────────────────────────────────────────────

def parse_amount(s):
    s = s.strip().replace(" ", "").replace(" ", "")
    if re.search(r",\d{2}$", s):          # dansk: 1.234,56
        s = s.replace(".", "").replace(",", ".")
    else:                                 # engelsk: 1,234.56
        s = s.replace(",", "")
    try:
        return Decimal(s).quantize(TWO)
    except InvalidOperation:
        return None


def parse_date(s):
    s = s.strip().lower().rstrip(".")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})$", s)
        if m:
            d, mo, y = map(int, m.groups())
        else:
            m = re.match(r"(\d{1,2})\.?\s+([a-zæøå]+)\.?\s+(\d{4})$", s)
            if not m or m.group(2) not in MONTHS:
                return None
            d, mo, y = int(m.group(1)), MONTHS[m.group(2)], int(m.group(3))
    if y < 100:
        y += 2000
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _labelled(text, labels, value_pattern, last=False, accept=None):
    """Værdien efter en etiket på samme linje (eller linjen under)."""
    found = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for label in labels:
            m = re.search(rf"(?i)\b{label}\b[\s.:#-]*(?:nr\.?|no\.?|nummer)?[\s.:#-]*({value_pattern})", line)
            if m and (accept is None or accept(m.group(1))):
                found.append(m.group(1))
                break
            if re.search(rf"(?i)\b{label}\b[\s.:#-]*$", line) and i + 1 < len(lines):
                m = re.match(rf"\s*({value_pattern})", lines[i + 1])
                if m and (accept is None or accept(m.group(1))):
                    found.append(m.group(1))
                    break
    if not found:
        return None
    return found[-1] if last else found[0]


BUYER_LINE = re.compile(r"(?i)^\s*(til|kunde|køber|faktureres til|leveres til|leveringsadresse|bill to|ship to|"
                        r"customer|kundenr|deres)\b")


def _cvrs(text):
    """CVR-numre i rækkefølge. Linjer med køberens oplysninger ("Til:", "Kunde:" …) springes over."""
    out = []
    for line in text.splitlines():
        if BUYER_LINE.match(line):
            continue
        for m in re.finditer(r"(?i)\b(?:CVR|SE|VAT|Moms|Momsnr|CVR-nr|CVR nr)\.?[\s.:-]*(?:nr\.?|no\.?|nummer)?"
                             r"[\s.:-]*(?:DK[\s-]?)?(\d{2}\s?\d{2}\s?\d{2}\s?\d{2})\b", line):
            cvr = re.sub(r"\s", "", m.group(1))
            if cvr not in out:
                out.append(cvr)
    return out


def _supplier_name(text, own_names):
    """Øverste linje, der ligner et firmanavn (ApS, A/S, I/S …), ellers første ikke-tomme linje."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    skip = re.compile(r"(?i)^(faktura|invoice|kreditnota|side|page|dato|kunde|til:|leveret til|ordre)")
    for l in lines[:25]:
        if re.search(r"(?i)\b(ApS|A/S|IVS|I/S|K/S|P/S|AMBA|Holding)\b", l) and not skip.match(l) \
                and not any(n and n.lower() in l.lower() for n in own_names):
            return re.split(r"\s{2,}|\s+CVR", l)[0].strip()[:200], "medium"
    for l in lines[:5]:
        if not skip.match(l) and not re.search(r"\d{4,}", l):
            return l[:200], "low"
    return "", "low"


LINE_RE = re.compile(
    rf"^(?P<desc>.+?)\s+(?P<qty>\d+(?:[.,]\d+)?)\s*(?:stk\.?|stk|pcs|timer|time|t\.?|kg|m2|m|ltr|l|md\.?|mdr\.?|"
    rf"enh\.?|x)?\s+(?P<unit>{AMOUNT})\s+(?:(?:\d{{1,2}}(?:,\d+)?\s?%)\s+)?(?P<amount>{AMOUNT})\s*(?:kr\.?|DKK)?$",
    re.I)
TOTAL_WORDS = re.compile(r"(?i)\b(i alt|total|subtotal|moms|at betale|netto|beløb|sum|rabat|fragt i alt|saldo)\b")


def _lines(text):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        m = LINE_RE.match(line)
        if not m or TOTAL_WORDS.search(m.group("desc")):
            continue
        try:
            qty = Decimal(m.group("qty").replace(",", "."))
        except InvalidOperation:
            continue
        unit, amount = parse_amount(m.group("unit")), parse_amount(m.group("amount"))
        if qty is None or unit is None or amount is None or qty == 0:
            continue
        # Antal × pris skal give linjebeløbet (± afrunding eller rabat på højst 1 %).
        if abs(qty * unit - amount) > max(Decimal("0.05"), abs(amount) / 100):
            continue
        out.append({"description": m.group("desc").strip(" .:-")[:500], "quantity": str(qty),
                    "unit_price": str(unit), "amount": str(amount)})
    return out


def _from_text(text, own_cvr="", source="pdf_text"):
    warnings, conf = [], {}
    own_names = []
    try:
        from core.models import CompanySettings
        cs = CompanySettings.objects.first()
        if cs:
            own_names = [cs.company_name]
            own_cvr = own_cvr or re.sub(r"\D", "", cs.tax_id or "")
    except Exception:  # noqa: BLE001 – kaldes også uden for et kundeskema i test
        pass

    cvrs = [c for c in _cvrs(text) if c != own_cvr]
    supplier_cvr = cvrs[0] if cvrs else ""
    conf["supplier"] = "high" if supplier_cvr else "low"
    if not supplier_cvr:
        warnings.append("Leverandørens CVR-nummer blev ikke fundet.")
    name, name_conf = _supplier_name(text, own_names)

    number = _labelled(text, ["fakturanummer", "fakturanr", "faktura nr", "faktura", "invoice number",
                              "invoice no", "invoice", "bilagsnr"], r"[A-Z0-9][A-Z0-9\-/]{0,29}",
                      accept=lambda v: bool(re.search(r"\d", v)))
    if number and not re.search(r"\d", number):
        number = None
    conf["number"] = "high" if number else "low"

    issue = _labelled(text, ["fakturadato", "faktura dato", "udstedt", "invoice date", "dato", "date"], DATE)
    due = _labelled(text, ["forfaldsdato", "forfald", "betalingsfrist", "betales senest", "sidste rettidige "
                           "betalingsdag", "due date", "betalingsdato"], DATE)
    issue_d, due_d = (parse_date(issue) if issue else None), (parse_date(due) if due else None)
    if not issue_d:
        all_dates = [parse_date(m.group(0)) for m in re.finditer(DATE, text, re.I)]
        all_dates = [d for d in all_dates if d]
        issue_d = all_dates[0] if all_dates else None
        conf["issue_date"] = "low"
        warnings.append("Fakturadatoen er gættet – tjek den.")
    else:
        conf["issue_date"] = "high"
    conf["due_date"] = "high" if due_d else "low"

    total = _labelled(text, ["total inkl\\.? moms", "i alt inkl\\.? moms", "at betale", "beløb at betale",
                             "total dkk", "i alt dkk", "total", "i alt"], AMOUNT, last=True)
    vat = _labelled(text, ["moms 25 ?%", "25 ?% moms", "heraf moms", "momsbeløb", "moms", "vat"], AMOUNT, last=True)
    net = _labelled(text, ["subtotal", "total ekskl\\.? moms", "i alt ekskl\\.? moms", "beløb ekskl\\.? moms",
                           "netto", "momsgrundlag"], AMOUNT, last=True)
    total_a, vat_a, net_a = (parse_amount(x) if x else None for x in (total, vat, net))
    if total_a is not None and vat_a is not None and net_a is None:
        net_a = total_a - vat_a
    if net_a is not None and vat_a is not None and total_a is None:
        total_a = net_a + vat_a
    if net_a is not None and total_a is not None and vat_a is None:
        vat_a = total_a - net_a
    totals_ok = None not in (net_a, vat_a, total_a) and abs(net_a + vat_a - total_a) <= TWO
    conf["totals"] = "high" if totals_ok else "low"
    if not totals_ok:
        warnings.append("Beløbene kunne ikke afstemmes (netto + moms = total). Tjek dem.")

    rate = None
    if totals_ok and net_a:
        if vat_a == 0:
            rate = Decimal("0")
        elif abs(vat_a - net_a * Decimal("0.25")) <= Decimal("0.02") + abs(net_a) / 1000:
            rate = Decimal("25")
        else:
            rate = (vat_a / net_a * 100).quantize(Decimal("1"))
        if vat_a == 0:
            warnings.append("Fakturaen har ingen moms – tjek om det er momsfrit køb eller omvendt betalingspligt "
                            "(EU-køb).")

    lines = _lines(text)
    if lines and net_a is not None:
        s = sum(Decimal(l["amount"]) for l in lines)
        if abs(s - net_a) <= Decimal("0.05"):
            conf["lines"] = "high"
        elif total_a is not None and abs(s - total_a) <= Decimal("0.05") and rate:
            # Linjerne er inkl. moms – omregn til ekskl. moms.
            factor = 1 + rate / 100
            for l in lines:
                l["unit_price"] = str((Decimal(l["unit_price"]) / factor).quantize(TWO))
                l["amount"] = str((Decimal(l["amount"]) / factor).quantize(TWO))
            conf["lines"] = "medium"
        else:
            warnings.append("Fakturalinjerne summer ikke til nettobeløbet. Der er lavet én linje med nettobeløbet.")
            lines = []
    if not lines:
        conf["lines"] = "low"
        if net_a is not None:
            lines = [{"description": f"Faktura {number or ''} {name}".strip()[:500], "quantity": "1",
                      "unit_price": str(net_a), "amount": str(net_a)}]
    for l in lines:
        l["tax_percent"] = str(rate if rate is not None else "")
        l["tax_category"] = "S" if rate else ("Z" if rate == 0 else "")

    currency = "EUR" if re.search(r"\bEUR\b|€", text) and not re.search(r"\bDKK\b|kr\.", text) else "DKK"
    iban = re.search(r"\b(DK\d{2}\s?(?:\d{4}\s?){3}\d{2})\b", text)
    fik = re.search(r"\+71<?\s?(\d{15})\s?\+\s?(\d{8})<?", text)
    parsed = {
        "document_type": "credit_note" if re.search(r"(?i)\bkreditnota\b", text[:500]) else "invoice",
        "format": "", "number": number or "", "currency": currency,
        "issue_date": issue_d.isoformat() if issue_d else None, "due_date": due_d.isoformat() if due_d else None,
        "supplier": {"name": name, "cvr": supplier_cvr, "gln": "", "name_confidence": name_conf},
        "lines": lines,
        "line_extension": str(net_a if net_a is not None else ""), "tax_exclusive": str(net_a or ""),
        "tax_total": str(vat_a if vat_a is not None else ""), "tax_inclusive": str(total_a or ""),
        "payable": str(total_a or ""),
        "payment_iban": re.sub(r"\s", "", iban.group(1)) if iban else "",
        "payment_id": f"+71<{fik.group(1)}+{fik.group(2)}<" if fik else "",
    }
    return {"source": source, "parsed": parsed, "confidence": conf, "warnings": warnings, "text": text[:20000]}


# ─── Forslag til regningen ───────────────────────────────────────────────────

def suggest(result):
    """Leverandør, konto og momskode – som for e-fakturaer, plus leverandørens seneste regning."""
    from einvoice.parse import find_tax_code, suggest_bill
    from purchases.models import BillLine

    parsed = result["parsed"]
    sug = suggest_bill(parsed)
    supplier_id = sug.get("supplier_id")
    last = (BillLine.objects.filter(bill__supplier_id=supplier_id).exclude(account=None)
            .select_related("bill").order_by("-bill__date").first()) if supplier_id else None
    from purchases.models import Supplier
    supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None
    for line in sug["lines"]:
        if not line.get("account_id"):
            acc = (last.account if last else None) or (supplier.default_account if supplier else None)
            if acc:
                line["account_id"], line["account_code"] = str(acc.id), acc.code
        if not line.get("tax_code_id"):
            tc = (last.tax_code if last else None) or (supplier.default_tax_code if supplier else None) \
                or find_tax_code(line.get("tax_percent") or 0, line.get("tax_category") or "")
            if tc:
                line["tax_code_id"], line["tax_code"] = str(tc.id), tc.code
    return sug
