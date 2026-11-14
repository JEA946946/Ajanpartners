"""Kundens indbakke: beskeder og bilagsforespørgsler fra revisorhuset.

/api/v1/inbox                 (X-Client) kundens synlige opgaver
/api/v1/inbox/<id>            én opgave med tråden
/api/v1/inbox/<id>/reply      svar (evt. med et bilag-id fra /api/v1/documents)

Kører i kundens skema (tenancy/middleware.py). Opgaverne ligger i public-skemaet
og filtreres altid på request.tenant, så en kunde kun ser sine egne.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import FirmTask, TaskMessage
from .views_work import message_dict, task_dict


def _err(message, code=400):
    return Response({"success": False, "message": message}, status=code)


def _inbox(request):
    if getattr(request, "tenant", None) is None or getattr(request, "client_access", None) is None:
        return None
    return FirmTask.objects.filter(client=request.tenant, visible_to_client=True).select_related(
        "client", "assigned_to", "created_by")


def _client_task(t, messages=False):
    d = task_dict(t, messages=messages)
    # Interne felter (hvem i huset, reference-id'er) er ok at vise; fjern kun huset-interne noter.
    d.pop("visible_to_client", None)
    return d


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inbox(request):
    qs = _inbox(request)
    if qs is None:
        return _err("Vælg en kunde.", 400)
    from django.db.models import Count
    qs = qs.annotate(n_messages=Count("messages"))
    status = request.query_params.get("status")
    if status == "active":
        qs = qs.exclude(status="closed")
    elif status:
        qs = qs.filter(status=status)
    items = [_client_task(t) for t in qs]
    return Response({"success": True, "data": {
        "tasks": items,
        "waiting": sum(1 for t in items if t["status"] == "open"),
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inbox_detail(request, pk):
    qs = _inbox(request)
    task = qs.filter(pk=pk).first() if qs is not None else None
    if task is None:
        return _err("Beskeden findes ikke", 404)
    return Response({"success": True, "data": {"task": _client_task(task, messages=True)}})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inbox_reply(request, pk):
    qs = _inbox(request)
    task = qs.filter(pk=pk).first() if qs is not None else None
    if task is None:
        return _err("Beskeden findes ikke", 404)
    if task.status == "closed":
        return _err("Sagen er lukket. Skriv til revisoren, hvis du vil genåbne den.")
    body = (request.data.get("body") or "").strip()
    document_id = (request.data.get("document_id") or "").strip()
    if not body and not document_id:
        return _err("Skriv et svar eller vedhæft et bilag")
    if document_id:
        import uuid
        from core.models import Document  # kundens skema
        try:
            uuid.UUID(document_id)
        except ValueError:
            return _err("Bilaget findes ikke")
        if not Document.objects.filter(pk=document_id).exists():
            return _err("Bilaget findes ikke")
    access = request.client_access
    msg = TaskMessage.objects.create(task=task, author=request.user, from_firm=access.is_firm,
                                     body=body or "Bilag vedhæftet.", document_id=document_id)
    if not access.is_firm:
        task.status = "answered"
        task.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": {"message": message_dict(msg),
                                               "task": _client_task(task, messages=True)}}, status=201)
