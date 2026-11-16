"""Dokumentskabeloner for revisorhuset: indlæsning, flettefelter og fletning.

Skabelonerne ligger som filer i firm/doc_templates/<kategori>/<id>.md (format: docs/skabeloner-format.md).
De er en del af koden (versioneret, gennemgået) – derfor bruges Djangos skabelonsprog, men uden
loaders og med et begrænset sæt tags.
"""

import calendar
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.db.models import Sum
from django.template import Context, Engine, TemplateSyntaxError
from django_tenants.utils import schema_context

from firm import branche

ROOT = Path(__file__).parent / "doc_templates"

CATEGORIES = [
    ("opdrag", "Opdrag og kundeaccept"),
    ("hvidvask", "Hvidvask og kundekendskab"),
    ("erklaeringer", "Erklæringer og påtegninger"),
    ("ledelse", "Ledelseserklæringer og kommunikation"),
    ("selskabsret", "Selskabsret og generalforsamling"),
    ("aarsafslutning", "Årsafslutning og revision"),
    ("skat", "Skat og moms"),
    ("kundebreve", "Kundebreve"),
]
KINDS = {"brev": "Brev", "erklaering": "Erklæring", "beslutning": "Beslutning", "arbejdspapir": "Arbejdspapir",
         "tjekliste": "Tjekliste"}
MONTHS = ["januar", "februar", "marts", "april", "maj", "juni", "juli", "august", "september", "oktober",
          "november", "december"]
CAPITAL = {"aps", "as", "ivs", "holding"}
PERSONAL = {"enk", "is", "pmv"}

ENGINE = Engine(autoescape=False, string_if_invalid="[…]", libraries={}, builtins=[
    "django.template.defaulttags", "django.template.defaultfilters"])
ALLOWED_TAGS = {"if", "elif", "else", "endif", "for", "empty", "endfor", "comment", "endcomment"}


class Missing(str):
    """Et tomt flettefelt: vises som [Ingen oplysning], men er falsk i {% if %}."""

    def __new__(cls, label="[…]"):
        return super().__new__(cls, label)

    def __bool__(self):
        return False


MISSING = Missing()


def _fill(value):
    if isinstance(value, dict):
        return {k: _fill(v) for k, v in value.items()}
    if value is None or value == "":
        return MISSING
    return value


# ---------------------------------------------------------------------------- indlæsning

_cache = {}


def _parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: mangler front matter")
    meta = json.loads(m.group(1))
    body = m.group(2)
    tags = set(re.findall(r"{%-?\s*(\w+)", body))
    if tags - ALLOWED_TAGS:
        raise ValueError(f"{path.name}: tags der ikke er tilladt: {', '.join(sorted(tags - ALLOWED_TAGS))}")
    return {
        "id": path.stem,
        "category": path.parent.name,
        "title": meta["title"],
        "description": meta.get("description", ""),
        "kind": meta.get("kind", "brev"),
        "references": meta.get("references", []),
        "legal_forms": meta.get("legal_forms", []),
        "industry_aware": bool(meta.get("industry_aware")),
        "fields": meta.get("fields", []),
        "body": body,
    }


def load_all():
    """Alle skabeloner, sorteret efter kategori og titel. Fejlbehæftede filer springes over (og logges)."""
    out, errors = [], []
    order = {c: i for i, (c, _) in enumerate(CATEGORIES)}
    for path in sorted(ROOT.glob("*/*.md")):
        if path.parent.name not in order:
            continue
        key = (path, path.stat().st_mtime)
        if key not in _cache:
            try:
                _cache[key] = _parse(path)
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                _cache[key] = {"error": str(e), "id": path.stem}
        item = _cache[key]
        (errors if "error" in item else out).append(item)
    out.sort(key=lambda t: (order[t["category"]], t["title"].lower()))
    return out, errors


def get(template_id):
    return next((t for t in load_all()[0] if t["id"] == template_id), None)


# ---------------------------------------------------------------------------- formatering

def da_date(d):
    return f"{d.day}. {MONTHS[d.month - 1]} {d.year}" if d else ""


def da_amount(value):
    if value is None:
        return ""
    q = Decimal(value).quantize(Decimal(1))
    s = f"{abs(q):,.0f}".replace(",", ".")
    return f"{'-' if q < 0 else ''}{s} kr."


def _add_months(d, months):
    y, m = divmod(d.month - 1 + months, 12)
    y += d.year
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def fiscal_years(client, today=None):
    """Regnskabsår for kunden: fra bogføringen hvis muligt, ellers beregnet ud fra startmåneden."""
    today = today or date.today()
    from accounts.models import FiscalYear

    try:
        with schema_context(client.schema_name):
            years = [{"id": str(y.id), "start": y.start_date, "end": y.end_date, "closed": y.is_closed}
                     for y in FiscalYear.objects.order_by("-start_date")]
    except Exception:  # noqa: BLE001 – skema uden bogføring (fx under oprettelse)
        years = []
    if years:
        return years
    m = client.fiscal_year_start_month or 1
    start = date(today.year if today.month >= m else today.year - 1, m, 1)
    out = []
    for i in range(-1, 3):  # næste år, indeværende og to tidligere
        s = date(start.year - i, m, 1)
        e = _add_months(s, 12) - date.resolution
        out.append({"id": s.isoformat(), "start": s, "end": e, "closed": False})
    return out


def default_year(years, today=None):
    """Seneste afsluttede regnskabsår – det er dét, de fleste dokumenter handler om."""
    today = today or date.today()
    ended = [y for y in years if y["end"] < today]
    return ended[0] if ended else (years[0] if years else None)


def year_label(start, end):
    return str(end.year) if start.year == end.year else f"{start.year}/{str(end.year)[2:]}"


def figures(client, start, end):
    """Nøgletal fra bogføringen for perioden (kun bogførte posteringer)."""
    from accounts.models import Account
    from journals.models import JournalEntryLine
    from firm.views_work import _amount_fields

    dr, cr = _amount_fields()
    with schema_context(client.schema_name):
        types = dict(Account.objects.values_list("id", "account_type__name"))
        posted = JournalEntryLine.objects.filter(journal_entry__is_posted=True)

        def net(qs):
            out = {}
            for r in qs.values("account_id").annotate(d=Sum(dr), c=Sum(cr)):
                t = (types.get(r["account_id"]) or "").lower()
                out[t] = out.get(t, Decimal(0)) + (r["d"] or 0) - (r["c"] or 0)
            return out

        period = posted.filter(journal_entry__date__gte=start, journal_entry__date__lte=end)
        pl = net(period.exclude(journal_entry__source="closing"))
        pl_all = net(period)
        bal = net(posted.filter(journal_entry__date__lte=end))
    if not bal and not pl:
        return {}
    revenue = -pl.get("revenue", Decimal(0))
    result = -(pl.get("revenue", Decimal(0)) + pl.get("expense", Decimal(0)))
    # Er året ikke lukket, ligger resultatet stadig på resultatkontiene.
    equity = -(bal.get("equity", Decimal(0)) + pl_all.get("revenue", Decimal(0)) + pl_all.get("expense", Decimal(0)))
    return {"omsaetning": da_amount(revenue), "resultat": da_amount(result),
            "balancesum": da_amount(bal.get("asset", Decimal(0))), "egenkapital": da_amount(equity)}


# ---------------------------------------------------------------------------- flettefelter

def _governing_body(form):
    return {"as": "bestyrelsen og direktionen", "aps": "direktionen", "ivs": "direktionen",
            "holding": "direktionen"}.get(form, "ledelsen")


def _owners(form):
    return {"aps": "anpartshaverne", "ivs": "anpartshaverne", "as": "aktionærerne"}.get(form, "kapitalejerne")


def build_context(firm, client=None, user=None, staff=None, year=None, with_figures=False, fields=None):
    today = date.today()
    ctx = {
        "firma": {"navn": firm.name, "cvr": firm.cvr,
                  # adresse = samlet linje (vej, postnr. og by), som skabelonerne bruger i brevhoved og underskrift
                  "adresse": ", ".join(p for p in (firm.address, f"{firm.zip_code} {firm.city}".strip()) if p),
                  "vej": firm.address, "postnr": firm.zip_code, "by": firm.city, "email": firm.email,
                  "telefon": firm.phone, "hjemmeside": firm.website},
        "medarbejder": {"navn": (user.get_full_name() or user.username) if user else "",
                        "titel": (staff.title if staff and staff.title else staff.get_role_display()) if staff else ""},
        "dato": {"idag": da_date(today), "aar": str(today.year)},
        "kunde": {}, "regnskab": {}, "branche": branche.context(""),
    }
    if client:
        form = client.legal_form
        responsible = client.responsible
        ctx["kunde"] = {
            "navn": client.name, "cvr": client.cvr, "adresse": client.address, "postnr": client.zip_code,
            "by": client.city, "email": client.email, "telefon": client.phone,
            "selskabsform": client.get_legal_form_display(), "selskabsform_kode": form,
            "er_kapitalselskab": form in CAPITAL, "er_personlig": form in PERSONAL,
            "ledelsesorgan": _governing_body(form), "kapitalejere": _owners(form),
            "branchekode": "", "branchetekst": "",
            "regnskabsklasse": client.accounting_class, "momsperiode": client.get_vat_period_display(),
            "ansvarlig": (responsible.get_full_name() or responsible.username) if responsible else "",
            "aftalereference": client.agreement_reference,
        }
        b = branche.context(client.industry_code)
        ctx["branche"] = b
        if b.get("titel"):
            from integrations.industry import describe

            info = describe(client.industry_code) or {}
            ctx["kunde"]["branchekode"] = info.get("display", client.industry_code)
            ctx["kunde"]["branchetekst"] = info.get("title", "")
        if year:
            from firm.deadlines import ANNUAL_REPORT_MONTHS, annual_report_due

            cls = (client.accounting_class or "B").upper()
            due = annual_report_due(year["end"], cls if cls in ANNUAL_REPORT_MONTHS else "B")
            ctx["regnskab"] = {
                "aar": year_label(year["start"], year["end"]), "start": da_date(year["start"]),
                "slut": da_date(year["end"]), "frist_aarsrapport": da_date(due),
                "omsaetning": "", "resultat": "", "balancesum": "", "egenkapital": "",
            }
            if with_figures:
                ctx["regnskab"].update(figures(client, year["start"], year["end"]))
    ctx = _fill(ctx)
    ctx["felt"] = _fill(fields or {})
    return ctx


def render_string(text, ctx):
    try:
        return ENGINE.from_string(text).render(Context(ctx, autoescape=False))
    except TemplateSyntaxError as e:
        raise ValueError(f"Fejl i skabelonen: {e}") from e


def field_defaults(template, ctx):
    out = {}
    for f in template["fields"]:
        d = f.get("default", "")
        if isinstance(d, str) and "{" in d:
            d = render_string(d, ctx)
            if d == str(MISSING):
                d = ""
        out[f["name"]] = d
    return out


def render(template, ctx, values=None):
    """Fletter skabelonen. Felter uden værdi får standardværdien eller vises som [Ingen oplysning]."""
    vals = field_defaults(template, ctx)
    for k, v in (values or {}).items():
        if k in vals:
            vals[k] = v
    for f in template["fields"]:
        if f.get("type") == "checkbox":
            vals[f["name"]] = vals[f["name"]] in (True, "true", "1", "ja", "on")
    ctx = {**ctx, "felt": _fill(vals)}
    text = render_string(template["body"], ctx)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text, vals
