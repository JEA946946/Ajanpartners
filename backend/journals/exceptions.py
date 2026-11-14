from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .models import ValidatedEntryError


def exception_handler(exc, context):
    """A change to a validated entry is a 400 with the reason, not a 500."""
    if isinstance(exc, ValidatedEntryError):
        return Response({"success": False, "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return drf_exception_handler(exc, context)
