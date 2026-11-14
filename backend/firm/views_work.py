"""Admin-portalen: fristkalender, opgaver/bilagsforespørgsler og revisorværktøjer.

/api/firm/deadlines                          beregnede frister for husets kunder
/api/firm/tasks[/<id>[/messages]]            opgaver og forespørgsler til kunderne
/api/firm/clients/<slug>/trial-balance       saldobalance (JSON eller CSV) – kræver aktiv grant
/api/firm/clients/<slug>/account-comments    revisorens kommentarer pr. konto – kræver aktiv grant
"""

import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.decorators import api_view, permission_classes

from core.permissions import IsFirmStaff
from tenancy.access import active_grant, staff_of

from .deadlines import deadline_dict, deadlines_for, profile_of
from .models import AccountComment, FirmTask, TaskMessage
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name

User = get_user_model()


def _parse_date(value, default):
    if not value:
        return default
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return default


# ─── Fristkalender ────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsFirmStaff])
def deadlines(request):
    """?from=&to= (standard: i dag + 90 dage), ?staff=<user_id> (ansvarlig eller tildelt),
    ?client=<slug>, ?kind=moms|a_skat|aarsrapport|selvangivelse|oplysningsskema|acontoskat."""
    staff = staff_of(request.user)
    today = timezone.localdate()
    start = _parse_date(request.query_params.get("from"), today)
    end = _parse_date(request.query_params.get("to"), start + timedelta(days=90))
    if end < start or (end - start).days > 800:
        return _err("Ugyldigt datointerval (højst ca. 2 år).")
    qs = _clients_for(staff).exclude(status="archived").prefetch_related("assignments__staff")
    qp = request.query_params
    if qp.get("client"):
        qs = qs.filter(slug=qp["client"])
    if qp.get("staff"):
        uid = qp["staff"]
        qs = qs.filter(Q(responsible_id=uid) | Q(assignments__staff__user_id=uid)).distinct()
    kinds = set(filter(None, qp.get("kind", "").split(",")))
    rows = []
    for client in qs:
        for d in deadlines_for(profile_of(client), start, end):
            if kinds and d.kind not in kinds:
                continue
            row = deadline_dict(d)
            row.update({"client": client.slug, "client_name": client.name, "cvr": client.cvr,
                        "responsible_id": client.responsible_id,
                        "responsible_name": _user_name(client.responsible)})
            rows.append(row)
    rows.sort(key=lambda r: (r["date"], r["client_name"]))
    return _ok({"from": start.isoformat(), "to": end.isoformat(), "deadlines": rows})


# ─── Opgaver og bilagsforespørgsler ───────────────────────────────────────────

def message_dict(m):
    return {"id": str(m.id), "author": _user_name(m.author), "from_firm": m.from_firm, "body": m.body,
            "document_id": m.document_id or None, "created_at": m.created_at.isoformat()}


def task_dict(t, messages=False):
    d = {
        "id": str(t.id), "client": t.client.slug, "client_name": t.client.name, "title": t.title,
        "description": t.description, "kind": t.kind, "kind_label": t.get_kind_display(),
        "reference_type": t.reference_type, "reference_id": t.reference_id,
        "reference_label": t.reference_label, "status": t.status, "status_label": t.get_status_display(),
        "visible_to_client": t.visible_to_client,
        "assigned_to": t.assigned_to_id, "assigned_name": _user_name(t.assigned_to),
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "created_by": _user_name(t.created_by), "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
    }
    if messages:
        d["messages"] = [message_dict(m) for m in t.messages.select_related("author")]
    else:
        d["message_count"] = getattr(t, "n_messages", None)
    return d


def _tasks_for(staff):
    return FirmTask.objects.filter(client__in=_clients_for(staff)).select_related(
        "client", "assigned_to", "created_by")


TASK_FIELDS = ("title", "description", "kind", "reference_type", "reference_id", "reference_label",
               "visible_to_client", "due_date", "status")


def _apply(task, data):
    for f in TASK_FIELDS:
        if f in data:
            value = data[f]
            if f == "due_date":
                value = value or None
            if f in ("kind", "status", "reference_type"):
                choices = dict({"kind": FirmTask.KINDS, "status": FirmTask.STATUS,
                                "reference_type": FirmTask.REF_TYPES}[f])
                if value not in choices:
                    return f"Ugyldig værdi for {f}"
            if value is None and f not in ("due_date", "visible_to_client"):
                value = ""
            setattr(task, f, value)
    if "assigned_to" in data:
        task.assigned_to = User.objects.filter(id=data["assigned_to"], firm_staff__isnull=False).first() \
            if data["assigned_to"] else None
    if task.status == "closed" and task.closed_at is None:
        task.closed_at = timezone.now()
    elif task.status != "closed":
        task.closed_at = None
    return None


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def tasks(request):
    staff = staff_of(request.user)
    if request.method == "GET":
        from django.db.models import Count
        qs = _tasks_for(staff).annotate(n_messages=Count("messages"))
        qp = request.query_params
        if qp.get("client"):
            qs = qs.filter(client__slug=qp["client"])
        if qp.get("status") == "active":
            qs = qs.exclude(status="closed")
        elif qp.get("status"):
            qs = qs.filter(status=qp["status"])
        if qp.get("kind"):
            qs = qs.filter(kind=qp["kind"])
        if qp.get("mine") == "1":
            qs = qs.filter(assigned_to=request.user)
        if qp.get("assigned_to"):
            qs = qs.filter(assigned_to_id=qp["assigned_to"])
        return _ok({"tasks": [task_dict(t) for t in qs[:500]]})

    data = request.data
    client = _clients_for(staff).filter(slug=data.get("client")).first()
    if client is None:
        return _err("Kunden findes ikke", 404)
    if not (data.get("title") or "").strip():
        return _err("Titel skal udfyldes")
    task = FirmTask(client=client, created_by=request.user, assigned_to=request.user)
    error = _apply(task, data)
    if error:
        return _err(error)
    task.save()
    if (data.get("message") or "").strip():
        TaskMessage.objects.create(task=task, author=request.user, from_firm=True, body=data["message"].strip())
    _log(request, "task_created", client, task=str(task.id), kind=task.kind)
    return _ok({"task": task_dict(task, messages=True)}, 201)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsFirmStaff])
def task_detail(request, pk):
    staff = staff_of(request.user)
    task = _tasks_for(staff).filter(pk=pk).first()
    if task is None:
        return _err("Opgaven findes ikke", 404)
    if request.method == "GET":
        return _ok({"task": task_dict(task, messages=True)})
    if request.method == "DELETE":
        if task.messages.filter(from_firm=False).exists():
            return _err("Opgaven har svar fra kunden og kan kun lukkes, ikke slettes.")
        _log(request, "task_deleted", task.client, task=str(task.id))
        task.delete()
        return _ok()
    error = _apply(task, request.data)
    if error:
        return _err(error)
    task.save()
    _log(request, "task_updated", task.client, task=str(task.id), status=task.status)
    return _ok({"task": task_dict(task, messages=True)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def task_message(request, pk):
    staff = staff_of(request.user)
    task = _tasks_for(staff).filter(pk=pk).first()
    if task is None:
        return _err("Opgaven findes ikke", 404)
    body = (request.data.get("body") or "").strip()
    if not body:
        return _err("Skriv en besked")
    TaskMessage.objects.create(task=task, author=request.user, from_firm=True, body=body,
                               document_id=request.data.get("document_id") or "")
    if task.status in ("answered", "in_progress") and task.visible_to_client:
        task.status = "open"  # afventer igen kunden
    task.save()
    _log(request, "task_message", task.client, task=str(task.id))
    return _ok({"task": task_dict(task, messages=True)}, 201)


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def task_document(request, pk, mid):
    """Hent et bilag, kunden har vedhæftet. Bilaget ligger i kundens skema → kræver grant."""
    staff = staff_of(request.user)
    task = _tasks_for(staff).filter(pk=pk).first()
    msg = task.messages.filter(pk=mid).first() if task else None
    if msg is None or not msg.document_id:
        return _err("Bilaget findes ikke", 404)
    if active_grant(task.client, staff) is None:
        return _err("Kunden har ikke givet adgang.", 403)
    from core.models import Document
    with schema_context(task.client.schema_name):
        doc = Document.objects.filter(pk=msg.document_id).first()
        if doc is None or not doc.file:
            return _err("Bilaget findes ikke", 404)
        fh = doc.file.open("rb")
        filename = doc.filename
    _log(request, "document_viewed", task.client, document=msg.document_id)
    return FileResponse(fh, as_attachment=True, filename=filename)


# ─── Revisorværktøjer ─────────────────────────────────────────────────────────

def _granted_client(request, slug):
    client, staff = _client_or_404(request, slug)
    if client is None:
        return None, _err("Kunden findes ikke", 404)
    if active_grant(client, staff) is None:
        return None, _err("Kunden har ikke givet adgang.", 403)
    return client, None


def _amount_fields():
    from journals.models import JournalEntryLine
    names = {f.name for f in JournalEntryLine._meta.get_fields()}
    if {"base_debit", "base_credit"} <= names:
        return "base_debit", "base_credit"
    return "debit", "credit"


def trial_balance_rows(start, end):
    """Saldobalance i det aktuelle skema: primo (før start), bevægelser i perioden og ultimo.
    Kun bogførte posteringer. Beløb i grundvalutaen (DKK)."""
    from accounts.models import Account
    from journals.models import JournalEntryLine

    dr, cr = _amount_fields()
    posted = JournalEntryLine.objects.filter(journal_entry__is_posted=True)

    def sums(qs):
        return {r["account_id"]: (r["d"] or Decimal(0)) - (r["c"] or Decimal(0))
                for r in qs.values("account_id").annotate(d=Sum(dr), c=Sum(cr))}

    def debit_credit(qs):
        return {r["account_id"]: (r["d"] or Decimal(0), r["c"] or Decimal(0))
                for r in qs.values("account_id").annotate(d=Sum(dr), c=Sum(cr))}

    opening = sums(posted.filter(journal_entry__date__lt=start))
    movement = debit_credit(posted.filter(journal_entry__date__gte=start, journal_entry__date__lte=end))
    rows = []
    for acc in Account.objects.filter(id__in=set(opening) | set(movement)).select_related("account_type") \
            .order_by("code"):
        o = opening.get(acc.id, Decimal(0))
        d, c = movement.get(acc.id, (Decimal(0), Decimal(0)))
        rows.append({
            "code": acc.code, "name": acc.name,
            "type": acc.account_type.name if acc.account_type_id else "",
            "arl_line": getattr(acc, "arl_line", "") or "",
            "opening": o, "debit": d, "credit": c, "closing": o + d - c,
        })
    return rows


def _da(amount):
    """1234.5 → 1234,50 (dansk CSV, uden tusindtalsseparator for at kunne importeres)."""
    return f"{amount:.2f}".replace(".", ",")


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def trial_balance(request, slug):
    """?from=&to= (standard: indeværende regnskabsår), ?export=csv."""
    client, error = _granted_client(request, slug)
    if error:
        return error
    from accounts.models import FiscalYear
    today = timezone.localdate()
    with schema_context(client.schema_name):
        years = list(FiscalYear.objects.order_by("-start_date").values("id", "name", "start_date", "end_date",
                                                                         "is_closed"))
        current = next((y for y in years if y["start_date"] <= today <= y["end_date"]), years[0] if years else None)
        default_start = current["start_date"] if current else date(today.year, 1, 1)
        default_end = current["end_date"] if current else date(today.year, 12, 31)
        start = _parse_date(request.query_params.get("from"), default_start)
        end = _parse_date(request.query_params.get("to"), default_end)
        rows = trial_balance_rows(start, end)
    comments = {}
    for c in AccountComment.objects.filter(client=client, resolved=False):
        comments[c.account_code] = comments.get(c.account_code, 0) + 1
    _log(request, "trial_balance_export" if request.query_params.get("export") == "csv" else "trial_balance_view",
         client, start=start.isoformat(), end=end.isoformat())

    if request.query_params.get("export") == "csv":
        buf = io.StringIO()
        buf.write("﻿")  # BOM, så Excel læser æøå
        w = csv.writer(buf, delimiter=";")
        w.writerow(["Kontonr", "Kontonavn", "Kontotype", "ÅRL-linje", "Primo", "Debet", "Kredit", "Ultimo"])
        for r in rows:
            w.writerow([r["code"], r["name"], r["type"], r["arl_line"], _da(r["opening"]), _da(r["debit"]),
                        _da(r["credit"]), _da(r["closing"])])
        resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = (f'attachment; filename="saldobalance_{client.cvr or client.slug}_'
                                       f'{start.isoformat()}_{end.isoformat()}.csv"')
        return resp

    return _ok({
        "from": start.isoformat(), "to": end.isoformat(),
        "fiscal_years": [{**y, "id": str(y["id"]), "start_date": y["start_date"].isoformat(),
                          "end_date": y["end_date"].isoformat()} for y in years],
        "rows": [{**r, **{k: str(r[k]) for k in ("opening", "debit", "credit", "closing")},
                  "open_comments": comments.get(r["code"], 0)} for r in rows],
        "totals": {k: str(sum((r[k] for r in rows), Decimal(0))) for k in ("opening", "debit", "credit", "closing")},
    })


def comment_dict(c):
    return {"id": str(c.id), "account_code": c.account_code, "fiscal_year": c.fiscal_year, "body": c.body,
            "resolved": c.resolved, "author": _user_name(c.author), "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()}


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def account_comments(request, slug):
    client, error = _granted_client(request, slug)
    if error:
        return error
    if request.method == "GET":
        qs = AccountComment.objects.filter(client=client).select_related("author")
        if request.query_params.get("account"):
            qs = qs.filter(account_code=request.query_params["account"])
        if request.query_params.get("fiscal_year"):
            qs = qs.filter(fiscal_year=request.query_params["fiscal_year"])
        return _ok({"comments": [comment_dict(c) for c in qs]})
    code = (request.data.get("account_code") or "").strip()
    body = (request.data.get("body") or "").strip()
    if not code or not body:
        return _err("Konto og kommentar skal udfyldes")
    c = AccountComment.objects.create(client=client, account_code=code, body=body, author=request.user,
                                      fiscal_year=request.data.get("fiscal_year") or None)
    _log(request, "account_comment", client, account=code)
    return _ok({"comment": comment_dict(c)}, 201)


@api_view(["PUT", "DELETE"])
@permission_classes([IsFirmStaff])
def account_comment_detail(request, slug, pk):
    client, error = _granted_client(request, slug)
    if error:
        return error
    c = AccountComment.objects.filter(client=client, pk=pk).first()
    if c is None:
        return _err("Kommentaren findes ikke", 404)
    if request.method == "DELETE":
        c.delete()
        return _ok()
    for f in ("body", "resolved"):
        if f in request.data:
            setattr(c, f, request.data[f])
    c.save()
    return _ok({"comment": comment_dict(c)})
