"""GET /api/v1/saft/export?from=ÅÅÅÅ-MM-DD&to=ÅÅÅÅ-MM-DD[&version=1.0|2.1] → XML-fil.

&check=1 giver i stedet tal og advarsler (fx manglende bankoplysninger) som JSON."""

from datetime import date

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import RoleWriteAccess
from integrations.base import setting

from .export import XSD, build_saft


def _err(message, code=400):
    return Response({"success": False, "message": message}, status=code)


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def export(request):
    from core.audit import log_action

    try:
        date_from = date.fromisoformat(request.query_params.get("from", ""))
        date_to = date.fromisoformat(request.query_params.get("to", ""))
    except ValueError:
        return _err("Angiv perioden som from=ÅÅÅÅ-MM-DD&to=ÅÅÅÅ-MM-DD.")
    version = request.query_params.get("version") or setting("SAFT_VERSION", "2.1")
    if version not in XSD:
        return _err(f"Ukendt SAF-T-version. Gyldige: {', '.join(XSD)}.")
    if (date_to - date_from).days > 731:
        return _err("Perioden må højst være to år.")
    try:
        xml, stats = build_saft(date_from, date_to, version, request.user)
    except ValueError as e:
        return _err(str(e))
    tenant = getattr(request, "tenant", None)
    cvr = getattr(tenant, "cvr", "") or "virksomhed"
    if request.query_params.get("check") in ("1", "true"):
        # Kun et tjek før udlevering: tal og advarsler som JSON, ingen fil og ingen log.
        return Response({"success": True, "data": {
            **{k: str(v) if hasattr(v, "quantize") else v for k, v in stats.items()}, "version": version}})
    log_action(request.user, "export", "SAF-T", f"{date_from}..{date_to}", {
        "version": version, "entries": stats["entries"], "accounts": stats["accounts"],
        "total_debit": str(stats["total_debit"]), "total_credit": str(stats["total_credit"]),
        "sales_invoices": stats.get("sales_invoices", 0), "purchase_invoices": stats.get("purchase_invoices", 0),
        "payments": stats.get("payments", 0), "warnings": stats.get("warnings", []),
    })
    resp = HttpResponse(xml, content_type="application/xml; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="SAF-T_{cvr}_{date_from}_{date_to}.xml"'
    if stats.get("warnings"):
        # Advarslerne står også i Header/HeaderComment i filen.
        resp["X-SAFT-Warnings"] = str(len(stats["warnings"]))
    return resp
