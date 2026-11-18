"""Admin-portalen: tidsregistrering, honoraraftaler og fakturaudkast i husets egen bogføring.

/api/firm/time                              GET (from, to, user, client, engagement) / POST
/api/firm/time/<id>                         PUT / DELETE (egne, ufakturerede – partner alle)
/api/firm/time/report                       GET (from, to) – partner
/api/firm/engagements/<id>/fee              GET / PUT {kind, hourly_rate, fixed_amount, note} (PUT: partner)
/api/firm/engagements/<id>/installments     POST {due_on, amount, text} (partner)
/api/firm/installments/<id>                 DELETE (partner, ufaktureret)
/api/firm/billing                           GET – ufaktureret pr. kunde (partner)
/api/firm/billing/own-client                POST {slug} | {create: true} (partner)
/api/firm/billing/clients/<slug>            GET – ufakturerede timer og rater
/api/firm/billing/clients/<slug>/draft      POST {entries, installments, date} → fakturaudkast

Fakturaen oprettes som *udkast* (sales.Invoice, status draft) i husets egen bogføring (Firm.own_client), så
nummer, moms, bogføring og afsendelse sker i det almindelige salgsflow. Timer og rater markeres med
fakturaens id; slettes udkastet i salgsflowet, frigives de igen (sync_invoices).
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.decorators import api_view, permission_classes

from core.permissions import IsFirmPartner, IsFirmStaff
from tenancy.access import ClientAccess, staff_of
from tenancy.models import ClientCompany, Firm, FirmStaff

from .models import Engagement, FeeAgreement, FeeInstallment, TimeEntry
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name

ZERO = Decimal("0")
CENT = Decimal("0.01")
SALES_VAT_CODE = "S01"  # salg med 25 % moms i husets kontoplan – kan ændres i udkastet


def _date(v):
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date() if v else None
    except ValueError:
        return None


def _dec(v, allow_none=True):
    if v in (None, ""):
        if allow_none:
            return None
        raise InvalidOperation
    d = Decimal(str(v).replace(",", "."))
    if d < 0:
        raise InvalidOperation
    return d.quantize(CENT, ROUND_HALF_UP)


def _hours(minutes):
    return (Decimal(minutes) / Decimal(60)).quantize(CENT, ROUND_HALF_UP)


def _value(e):
    return (Decimal(e.minutes) * e.rate / Decimal(60)).quantize(CENT, ROUND_HALF_UP)


def rate_for(user, engagement=None):
    """Timepris: honoraraftalens sats > medarbejderens sats > husets standardsats > 0."""
    fee = getattr(engagement, "fee", None) if engagement else None
    if fee is not None and fee.hourly_rate is not None:
        return fee.hourly_rate
    staff = FirmStaff.objects.filter(user=user).first()
    if staff and staff.hourly_rate is not None:
        return staff.hourly_rate
    return Firm.current().default_hourly_rate or ZERO


def _fee_kind(engagement):
    fee = getattr(engagement, "fee", None) if engagement else None
    return fee.kind if fee else "timepris"


def _billable_for_invoice(e):
    """Timer, der faktureres som medgået tid (ikke ved fast pris og ikke husets interne tid)."""
    return e.billable and _fee_kind(e.engagement) != "fast"


def entry_dict(e):
    return {
        "id": str(e.id), "user_id": e.user_id, "user": _user_name(e.user), "client": e.client.slug,
        "client_name": e.client.name, "engagement": str(e.engagement_id) if e.engagement_id else None,
        "engagement_title": (e.engagement.title or e.engagement.get_kind_display()) if e.engagement_id else None,
        "date": e.date.isoformat(), "minutes": e.minutes, "hours": str(_hours(e.minutes)),
        "activity": e.activity, "note": e.note, "billable": e.billable, "rate": str(e.rate),
        "value": str(_value(e)), "invoiced": e.invoice_id is not None,
        "fixed_price": _fee_kind(e.engagement) == "fast",
    }


def installment_dict(i):
    return {"id": str(i.id), "engagement": str(i.engagement_id), "due_on": i.due_on.isoformat(),
            "amount": str(i.amount), "text": i.text, "invoiced": i.invoice_id is not None,
            "offset": i.offset_invoice_id is not None}


def _allowed_clients(staff):
    """Kunder, man må registrere tid på: ens kunder og husets egen bogføring (intern tid)."""
    own = Firm.current().own_client_id
    return ClientCompany.objects.filter(Q(pk__in=_clients_for(staff).values("pk")) | Q(pk=own))


def _entries_qs():
    return TimeEntry.objects.select_related("user", "client", "engagement__fee")


# ─── Synkronisering med husets bøger ──────────────────────────────────────────

def own_invoices(ids):
    """{invoice_id: {number, status}} for de id'er, der findes i husets bøger."""
    own = Firm.current().own_client
    if own is None or not ids:
        return {}
    from sales.models import Invoice
    with schema_context(own.schema_name):
        return {str(i["id"]): {"number": i["invoice_number"], "status": i["status"]}
                for i in Invoice.objects.filter(id__in=list(ids)).values("id", "invoice_number", "status")}


def sync_invoices():
    """Frigiv timer og rater, hvis fakturaudkastet er slettet i husets bøger."""
    if Firm.current().own_client_id is None:
        return
    ids = set(TimeEntry.objects.exclude(invoice_id=None).values_list("invoice_id", flat=True))
    ids |= set(FeeInstallment.objects.exclude(invoice_id=None).values_list("invoice_id", flat=True))
    ids |= set(FeeInstallment.objects.exclude(offset_invoice_id=None).values_list("offset_invoice_id", flat=True))
    existing = set(own_invoices({str(i) for i in ids}))
    gone = [i for i in ids if str(i) not in existing]
    if not gone:
        return
    TimeEntry.objects.filter(invoice_id__in=gone).update(invoice_id=None, invoiced_at=None)
    FeeInstallment.objects.filter(invoice_id__in=gone).update(invoice_id=None, invoiced_at=None)
    FeeInstallment.objects.filter(offset_invoice_id__in=gone).update(offset_invoice_id=None)


# ─── Tidsregistrering ─────────────────────────────────────────────────────────

def _apply_entry(request, staff, e, d, creating):
    """Validér og sæt felter. Returnerer fejltekst eller None."""
    if creating or "client" in d:
        client = _allowed_clients(staff).filter(slug=d.get("client") or "").first()
        if client is None:
            return "Vælg en kunde"
        e.client = client
    if creating or "engagement" in d:
        eng = None
        if d.get("engagement"):
            eng = Engagement.objects.filter(pk=d["engagement"], client=e.client).select_related("fee").first()
            if eng is None:
                return "Opdraget hører ikke til kunden"
        e.engagement = eng
    elif e.engagement_id and e.engagement.client_id != e.client_id:
        e.engagement = None
    if creating or "date" in d:
        e.date = _date(d.get("date"))
        if e.date is None:
            return "Angiv dato"
    if creating or "minutes" in d:
        try:
            e.minutes = int(d.get("minutes") or 0)
        except (TypeError, ValueError):
            return "Ugyldigt antal minutter"
        if not 1 <= e.minutes <= 24 * 60:
            return "Tiden skal være mellem 1 minut og 24 timer"
    for f in ("activity", "note"):
        if f in d:
            setattr(e, f, str(d[f] or "").strip()[:100 if f == "activity" else 4000])
    if "billable" in d:
        e.billable = bool(d["billable"])
    elif creating:
        e.billable = e.client_id != Firm.current().own_client_id
    if "rate" in d and d["rate"] not in (None, "") and staff.is_partner:
        try:
            e.rate = _dec(d["rate"], allow_none=False)
        except InvalidOperation:
            return "Ugyldig timepris"
    elif creating or "engagement" in d or "client" in d:
        e.rate = rate_for(e.user, e.engagement)
    return None


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def time_entries(request):
    staff = staff_of(request.user)
    if request.method == "GET":
        qp = request.query_params
        qs = _entries_qs()
        uid = qp.get("user")
        if uid == "all" and staff.is_partner:
            pass
        elif uid and staff.is_partner:
            qs = qs.filter(user_id=uid)
        else:
            qs = qs.filter(user=request.user)
        if _date(qp.get("from")):
            qs = qs.filter(date__gte=_date(qp["from"]))
        if _date(qp.get("to")):
            qs = qs.filter(date__lte=_date(qp["to"]))
        if qp.get("client"):
            qs = qs.filter(client__slug=qp["client"])
        if qp.get("engagement"):
            qs = qs.filter(engagement_id=qp["engagement"])
        rows = list(qs[:2000])
        return _ok({"entries": [entry_dict(e) for e in rows],
                    "total_minutes": sum(e.minutes for e in rows),
                    "billable_minutes": sum(e.minutes for e in rows if e.billable)})
    d = request.data
    user = request.user
    if d.get("user_id") and staff.is_partner and str(d["user_id"]) != str(request.user.id):
        other = FirmStaff.objects.filter(user_id=d["user_id"], is_active=True).select_related("user").first()
        if other is None:
            return _err("Ukendt medarbejder")
        user = other.user
    e = TimeEntry(user=user)
    msg = _apply_entry(request, staff, e, d, creating=True)
    if msg:
        return _err(msg)
    e.save()
    _log(request, "time_created", e.client, entry=str(e.id), minutes=e.minutes)
    return _ok({"entry": entry_dict(_entries_qs().get(pk=e.pk))}, 201)


@api_view(["PUT", "DELETE"])
@permission_classes([IsFirmStaff])
def time_entry_detail(request, pk):
    staff = staff_of(request.user)
    e = _entries_qs().filter(pk=pk).first()
    if e is None or (e.user_id != request.user.id and not staff.is_partner):
        return _err("Registreringen findes ikke", 404)
    if e.invoice_id:
        return _err("Tiden er faktureret og kan ikke ændres. Slet fakturaudkastet i husets bøger for at frigive den.",
                    409)
    if request.method == "DELETE":
        client = e.client
        e.delete()
        _log(request, "time_deleted", client, entry=str(pk))
        return _ok({})
    msg = _apply_entry(request, staff, e, request.data, creating=False)
    if msg:
        return _err(msg)
    e.save()
    _log(request, "time_updated", e.client, entry=str(e.id))
    return _ok({"entry": entry_dict(_entries_qs().get(pk=e.pk))})


@api_view(["GET"])
@permission_classes([IsFirmPartner])
def time_report(request):
    """Tid pr. medarbejder, kunde og opdrag i perioden + budget mod forbrug på åbne opdrag."""
    sync_invoices()
    today = timezone.localdate()
    start = _date(request.query_params.get("from")) or today.replace(day=1)
    end = _date(request.query_params.get("to")) or today
    own = Firm.current().own_client_id
    rows = list(_entries_qs().filter(date__gte=start, date__lte=end))

    by_staff = defaultdict(lambda: {"minutes": 0, "billable_minutes": 0, "internal_minutes": 0, "value": ZERO})
    by_client = defaultdict(lambda: {"minutes": 0, "value": ZERO, "invoiced": ZERO, "unbilled": ZERO})
    for e in rows:
        s = by_staff[e.user_id]
        s["name"] = _user_name(e.user)
        s["minutes"] += e.minutes
        if e.client_id == own:
            s["internal_minutes"] += e.minutes
        elif e.billable:
            s["billable_minutes"] += e.minutes
            s["value"] += _value(e)
        if e.client_id == own:
            continue
        c = by_client[e.client_id]
        c.update(slug=e.client.slug, name=e.client.name)
        c["minutes"] += e.minutes
        if e.billable:
            c["value"] += _value(e)
            if e.invoice_id:
                c["invoiced"] += _value(e)
            elif _billable_for_invoice(e):
                c["unbilled"] += _value(e)

    # Budget mod forbrug (al registreret tid på opdraget, ikke kun perioden)
    staff = staff_of(request.user)
    used = defaultdict(int)
    for eng_id, minutes in TimeEntry.objects.exclude(engagement=None).values_list("engagement_id", "minutes"):
        used[eng_id] += minutes
    engagements = []
    for eng in Engagement.objects.filter(client__in=_clients_for(staff)).exclude(status="leveret").select_related(
            "client", "fee"):
        if not (eng.budget_hours or used.get(eng.id)):
            continue
        engagements.append({
            "id": str(eng.id), "client_name": eng.client.name, "title": eng.title or eng.get_kind_display(),
            "budget_hours": str(eng.budget_hours) if eng.budget_hours is not None else None,
            "used_hours": str(_hours(used.get(eng.id, 0))), "fee_kind": _fee_kind(eng),
        })

    def fmt(d):
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in d.items()}

    staff_rows = []
    for uid, s in by_staff.items():
        rate = (Decimal(100) * s["billable_minutes"] / s["minutes"]).quantize(Decimal("0.1")) if s["minutes"] else ZERO
        staff_rows.append(fmt({"user_id": uid, **s, "hours": _hours(s["minutes"]),
                               "billable_hours": _hours(s["billable_minutes"]), "billable_pct": rate}))
    return _ok({"from": start.isoformat(), "to": end.isoformat(),
                "staff": sorted(staff_rows, key=lambda r: r["name"] or ""),
                "clients": sorted([fmt({**c, "hours": _hours(c["minutes"])}) for c in by_client.values()],
                                  key=lambda r: r["name"]),
                "engagements": engagements})


# ─── Honoraraftale ────────────────────────────────────────────────────────────

def _engagement(request, pk):
    staff = staff_of(request.user)
    return Engagement.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related("client").first(), staff


def fee_dict(eng):
    fee = FeeAgreement.objects.filter(engagement=eng).first()
    minutes = list(TimeEntry.objects.filter(engagement=eng).values_list("minutes", "billable", "rate", "invoice_id"))
    return {
        "fee": {"kind": fee.kind if fee else "timepris", "kind_label": fee.get_kind_display() if fee else "Medgået tid",
                "hourly_rate": str(fee.hourly_rate) if fee and fee.hourly_rate is not None else None,
                "fixed_amount": str(fee.fixed_amount) if fee and fee.fixed_amount is not None else None,
                "note": fee.note if fee else ""},
        "kinds": [{"value": k, "label": v} for k, v in FeeAgreement.KINDS],
        "installments": [installment_dict(i) for i in eng.installments.all()],
        "time": {
            "hours": str(_hours(sum(m for m, *_ in minutes))),
            "billable_value": str(sum(((Decimal(m) * r / 60).quantize(CENT, ROUND_HALF_UP)
                                       for m, b, r, _ in minutes if b), ZERO)),
            "invoiced_value": str(sum(((Decimal(m) * r / 60).quantize(CENT, ROUND_HALF_UP)
                                       for m, b, r, inv in minutes if b and inv), ZERO)),
            "budget_hours": str(eng.budget_hours) if eng.budget_hours is not None else None,
        },
    }


@api_view(["GET", "PUT"])
@permission_classes([IsFirmStaff])
def engagement_fee(request, pk):
    eng, staff = _engagement(request, pk)
    if eng is None:
        return _err("Opdraget findes ikke", 404)
    if request.method == "PUT":
        if not staff.is_partner:
            return _err("Kun partnere kan ændre honoraraftalen.", 403)
        d = request.data
        fee, _ = FeeAgreement.objects.get_or_create(engagement=eng)
        if "kind" in d:
            if d["kind"] not in dict(FeeAgreement.KINDS):
                return _err("Ugyldig aftaletype")
            fee.kind = d["kind"]
        try:
            if "hourly_rate" in d:
                fee.hourly_rate = _dec(d["hourly_rate"])
            if "fixed_amount" in d:
                fee.fixed_amount = _dec(d["fixed_amount"])
        except InvalidOperation:
            return _err("Ugyldigt beløb")
        if "note" in d:
            fee.note = str(d["note"] or "").strip()
        fee.save()
        _log(request, "fee_updated", eng.client, engagement=str(eng.id), kind=fee.kind)
    return _ok(fee_dict(eng))


@api_view(["POST"])
@permission_classes([IsFirmPartner])
def engagement_installments(request, pk):
    eng, _ = _engagement(request, pk)
    if eng is None:
        return _err("Opdraget findes ikke", 404)
    if _fee_kind(eng) == "timepris":
        return _err("Rater bruges ved fast pris eller aconto. Skift honoraraftalen først.")
    due = _date(request.data.get("due_on"))
    try:
        amount = _dec(request.data.get("amount"), allow_none=False)
    except InvalidOperation:
        return _err("Ugyldigt beløb")
    if due is None or amount <= 0:
        return _err("Angiv dato og et beløb større end 0")
    FeeInstallment.objects.create(engagement=eng, due_on=due, amount=amount,
                                  text=str(request.data.get("text") or "").strip()[:255])
    _log(request, "installment_created", eng.client, engagement=str(eng.id), amount=str(amount))
    return _ok(fee_dict(eng), 201)


@api_view(["DELETE"])
@permission_classes([IsFirmPartner])
def installment_detail(request, pk):
    staff = staff_of(request.user)
    i = FeeInstallment.objects.filter(pk=pk, engagement__client__in=_clients_for(staff)).select_related(
        "engagement__client").first()
    if i is None:
        return _err("Raten findes ikke", 404)
    if i.invoice_id:
        return _err("Raten er faktureret og kan ikke slettes.", 409)
    eng = i.engagement
    i.delete()
    _log(request, "installment_deleted", eng.client, engagement=str(eng.id))
    return _ok(fee_dict(eng))


# ─── Fakturering ──────────────────────────────────────────────────────────────

def _own_dict(firm):
    own = firm.own_client
    return {"slug": own.slug, "name": own.name, "cvr": own.cvr} if own else None


def _unbilled(client):
    entries = [e for e in _entries_qs().filter(client=client, invoice_id=None) if _billable_for_invoice(e)]
    insts = list(FeeInstallment.objects.filter(engagement__client=client, invoice_id=None).select_related(
        "engagement"))
    return entries, insts


@api_view(["GET"])
@permission_classes([IsFirmPartner])
def billing(request):
    sync_invoices()
    firm = Firm.current()
    today = timezone.localdate()
    totals = defaultdict(lambda: {"minutes": 0, "time_value": ZERO, "installments": ZERO, "due_installments": 0})
    names = {}
    for e in _entries_qs().filter(invoice_id=None, billable=True).exclude(client_id=firm.own_client_id):
        if not _billable_for_invoice(e):
            continue
        t = totals[e.client_id]
        names[e.client_id] = (e.client.slug, e.client.name)
        t["minutes"] += e.minutes
        t["time_value"] += _value(e)
        t.setdefault("oldest", e.date)
        t["oldest"] = min(t["oldest"], e.date)
    for i in FeeInstallment.objects.filter(invoice_id=None).select_related("engagement__client"):
        t = totals[i.engagement.client_id]
        names[i.engagement.client_id] = (i.engagement.client.slug, i.engagement.client.name)
        t["installments"] += i.amount
        if i.due_on <= today:
            t["due_installments"] += 1
    rows = []
    for cid, t in totals.items():
        slug, name = names[cid]
        rows.append({"client": slug, "client_name": name, "hours": str(_hours(t["minutes"])),
                     "time_value": str(t["time_value"]), "installments": str(t["installments"]),
                     "due_installments": t["due_installments"],
                     "oldest": t["oldest"].isoformat() if t.get("oldest") else None,
                     "total": str(t["time_value"] + t["installments"])})
    return _ok({"own_client": _own_dict(firm), "clients": sorted(rows, key=lambda r: r["client_name"]),
                "default_hourly_rate": str(firm.default_hourly_rate) if firm.default_hourly_rate is not None else None})


@api_view(["POST"])
@permission_classes([IsFirmPartner])
def billing_own_client(request):
    """Vælg (eller opret) den kunde i systemet, der er husets egen bogføring."""
    firm = Firm.current()
    if request.data.get("create"):
        if firm.own_client_id:
            return _err("Husets egen bogføring er allerede valgt.")
        if not firm.cvr:
            return _err("Angiv revisorhusets CVR-nummer under Revisorhuset først.")
        existing = ClientCompany.objects.filter(cvr=firm.cvr).exclude(schema_name="public").first()
        if existing:
            return _err(f"Der findes allerede en kunde med CVR {firm.cvr} ({existing.name}). Vælg den i stedet.")
        from tenancy.services import create_client
        client, _ = create_client(name=firm.name, package_code="pro", created_by=request.user, cvr=firm.cvr,
                                  address=firm.address, zip_code=firm.zip_code, city=firm.city, email=firm.email,
                                  phone=firm.phone, legal_form="andet")
        _seed_company_settings(client, firm)
    else:
        client = ClientCompany.objects.exclude(schema_name="public").filter(slug=request.data.get("slug") or "").first()
        if client is None:
            return _err("Kunden findes ikke")
        if client.status == "archived":
            return _err("Kunden er arkiveret.")
        if TimeEntry.objects.filter(client=client, billable=True).exists():
            return _err("Kunden har fakturerbar tid registreret og kan ikke være husets egen bogføring.")
    firm.own_client = client
    firm.save(update_fields=["own_client"])
    _log(request, "own_client_set", client)
    return _ok({"own_client": _own_dict(firm)})


def _seed_company_settings(client, firm):
    """Husets stamdata som afsender på fakturaerne (kan rettes under Indstillinger i bogføringen)."""
    from core.models import CompanySettings
    with schema_context(client.schema_name):
        s = CompanySettings.objects.first() or CompanySettings()
        s.company_name = s.company_name or firm.name
        s.tax_id = s.tax_id or firm.cvr
        s.address = s.address or firm.address
        s.city = s.city or f"{firm.zip_code} {firm.city}".strip()
        s.email = s.email or firm.email
        s.phone = s.phone or firm.phone
        s.save()


@api_view(["GET"])
@permission_classes([IsFirmPartner])
def billing_client(request, slug):
    sync_invoices()
    client, _ = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    entries, insts = _unbilled(client)
    return _ok({"client": {"slug": client.slug, "name": client.name, "cvr": client.cvr},
                "entries": [entry_dict(e) for e in entries],
                "installments": [{**installment_dict(i), "engagement_title": i.engagement.title
                                  or i.engagement.get_kind_display(), "kind": _fee_kind(i.engagement)}
                                 for i in insts],
                "own_client": _own_dict(Firm.current())})


def _customer_for(client):
    """Debitoren i husets bøger ud fra kundens CVR (oprettes, hvis den mangler)."""
    from journals.numbering import next_number
    from sales.models import Customer
    if client.cvr:
        c = Customer.objects.filter(tax_id__in=[client.cvr, f"DK{client.cvr}", f"DK {client.cvr}"]).first()
        if c:
            return c
    c = Customer.objects.filter(name=client.name, tax_id="").first() if not client.cvr else None
    if c:
        return c
    return Customer.objects.create(code=next_number(Customer, "code", "CUS"), name=client.name,
                                   email=client.email or "", phone=client.phone or "",
                                   address=client.address or "", postal_code=client.zip_code or "",
                                   city=client.city or "", tax_id=client.cvr or "", is_business=True)


def _period(entries):
    ds = [e.date for e in entries]
    a, b = min(ds), max(ds)
    return a.strftime("%d.%m.%Y") if a == b else f"{a.strftime('%d.%m.%Y')}–{b.strftime('%d.%m.%Y')}"


def _eng_title(eng):
    if eng is None:
        return "Øvrig assistance"
    from . import templating
    year = templating.year_label(eng.year_start, eng.year_end) if eng.year_start and eng.year_end else ""
    return f"{eng.title or eng.get_kind_display()}{' ' + year if year else ''}"


def build_lines(entries, insts, already_offset_ids=()):
    """Fakturalinjer: pr. opdrag en tekstlinje, medgået tid pr. timepris, rater, og modregning af aconto.

    Aconto modregnes med hele rater, så længe summen ikke overstiger den medgåede tid på opdraget.
    Returnerer (linjer, rater der modregnes)."""
    groups = defaultdict(lambda: {"entries": [], "insts": []})
    for e in entries:
        groups[e.engagement_id]["entries"].append(e)
    for i in insts:
        groups[i.engagement_id]["insts"].append(i)
    lines, offsets = [], []
    order = sorted(groups.items(), key=lambda kv: _eng_title((kv[1]["entries"] or kv[1]["insts"])[0].engagement))
    for eng_id, g in order:
        eng = (g["entries"] or g["insts"])[0].engagement
        lines.append({"description": _eng_title(eng), "is_text": True})
        by_rate = defaultdict(list)
        for e in g["entries"]:
            by_rate[e.rate].append(e)
        time_value = ZERO
        for rate, es in sorted(by_rate.items()):
            minutes = sum(e.minutes for e in es)
            lines.append({"description": f"Medgået tid {_period(es)}", "quantity": _hours(minutes),
                          "unit": "timer", "unit_price": rate})
            time_value += (_hours(minutes) * rate).quantize(CENT, ROUND_HALF_UP)
        for i in g["insts"]:
            label = "Aconto" if _fee_kind(eng) == "aconto" else "Honorar"
            lines.append({"description": i.text or f"{label} (rate {i.due_on.strftime('%d.%m.%Y')})",
                          "quantity": Decimal(1), "unit": "stk.", "unit_price": i.amount})
        if eng is not None and _fee_kind(eng) == "aconto" and g["entries"]:
            room, used = time_value, []
            for a in FeeInstallment.objects.filter(engagement=eng, offset_invoice_id=None).exclude(
                    invoice_id=None).exclude(pk__in=list(already_offset_ids)).order_by("due_on"):
                if a.amount <= room:
                    room -= a.amount
                    used.append(a)
            if used:
                total = sum((a.amount for a in used), ZERO)
                lines.append({"description": "Modregning af faktureret aconto", "quantity": Decimal(1),
                              "unit": "stk.", "unit_price": -total})
                offsets += used
    return lines, offsets


@api_view(["POST"])
@permission_classes([IsFirmPartner])
def billing_draft(request, slug):
    sync_invoices()
    firm = Firm.current()
    own = firm.own_client
    if own is None:
        return _err("Vælg husets egen bogføring under Fakturering først.")
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if client.pk == own.pk:
        return _err("Husets egen bogføring kan ikke faktureres.")
    entry_ids = [str(x) for x in request.data.get("entries") or []]
    inst_ids = [str(x) for x in request.data.get("installments") or []]
    entries = [e for e in _entries_qs().filter(client=client, invoice_id=None, pk__in=entry_ids)
               if _billable_for_invoice(e)]
    insts = list(FeeInstallment.objects.filter(engagement__client=client, invoice_id=None, pk__in=inst_ids)
                 .select_related("engagement"))
    if len(entries) != len(set(entry_ids)) or len(insts) != len(set(inst_ids)):
        return _err("Nogle af de valgte timer eller rater er allerede faktureret. Opdatér siden.", 409)
    if not entries and not insts:
        return _err("Vælg mindst én registrering eller rate.")
    if any(e.rate <= 0 for e in entries):
        return _err("Nogle timer har ingen timepris. Angiv en sats på medarbejderen, opdraget eller huset.")
    on = _date(request.data.get("date")) or timezone.localdate()
    lines, offsets = build_lines(entries, insts)
    if sum((Decimal(l.get("quantity", 0)) * Decimal(l.get("unit_price", 0)) for l in lines if not l.get("is_text")),
           ZERO) <= 0:
        return _err("Fakturaens beløb skal være større end 0.")

    from core import audit
    from core.models import TaxCode
    from sales import invoicing
    from sales.models import Invoice, InvoiceLine
    from tenancy.context import current_access

    token = current_access.set(ClientAccess(own, "admin", "firm", staff))
    try:
        with schema_context(own.schema_name), transaction.atomic():
            customer = _customer_for(client)
            tax = TaxCode.objects.filter(code=SALES_VAT_CODE).first()
            inv = Invoice.objects.create(
                invoice_number=invoicing.draft_number(), customer=customer, date=on,
                due_date=invoicing.due_date_for(on, customer.payment_terms_code),
                payment_terms_code=customer.payment_terms_code, created_by=_user_name(request.user) or "",
                notes=str(request.data.get("notes") or "").strip())
            for pos, l in enumerate(lines):
                if l.get("is_text"):
                    InvoiceLine.objects.create(invoice=inv, description=l["description"][:500], quantity=0,
                                               unit_price=0, is_text=True, position=pos)
                else:
                    InvoiceLine.objects.create(invoice=inv, description=l["description"][:500],
                                               quantity=l["quantity"], unit=l["unit"], unit_price=l["unit_price"],
                                               tax_code=tax, position=pos)
            invoicing.refresh_totals(inv)
            audit.log_action(request.user, "create", "Invoice", inv.id,
                             {"from_firm_billing": client.slug, "entries": len(entries), "installments": len(insts)})
            result = {"has_vat_code": tax is not None, "id": str(inv.id), "number": inv.invoice_number, "subtotal": str(inv.subtotal),
                      "tax": str(inv.tax_amount), "total": str(inv.total), "customer": customer.name}
    finally:
        current_access.reset(token)

    now = timezone.now()
    TimeEntry.objects.filter(pk__in=[e.pk for e in entries]).update(invoice_id=result["id"], invoiced_at=now)
    FeeInstallment.objects.filter(pk__in=[i.pk for i in insts]).update(invoice_id=result["id"], invoiced_at=now)
    FeeInstallment.objects.filter(pk__in=[a.pk for a in offsets]).update(offset_invoice_id=result["id"])
    _log(request, "invoice_draft_created", client, invoice=result["id"], total=result["total"])
    _log(request, "invoice_draft_created", own, invoice=result["id"], for_client=client.slug)
    warning = None if result.pop("has_vat_code") else (
        f"Momskoden {SALES_VAT_CODE} findes ikke i husets kontoplan – vælg momskode på linjerne i udkastet.")
    return _ok({"invoice": result, "own_client": _own_dict(firm), "warning": warning}, 201)
