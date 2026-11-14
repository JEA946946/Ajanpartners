"""Login med to-faktor, egen adgangskode og MFA-opsætning (public).

/api/v1/auth/login        trin 1: brugernavn + adgangskode → JWT, eller mfa_required + mfa_token
/api/v1/auth/mfa/verify   trin 2: mfa_token + kode → JWT
/api/v1/me/mfa            status, setup, confirm, disable
/api/v1/me/password       skift egen adgangskode (Djangos validatorer)
"""

import bcrypt
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.views import AuthRateThrottle, _find_login_user, _user_dict

from . import mfa
from .models import FirmAuditLog


def _ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[-1].strip() if fwd else request.META.get("REMOTE_ADDR")


def _err(message, code=status.HTTP_400_BAD_REQUEST, **extra):
    return Response({"success": False, "message": message, **extra}, status=code)


def _tokens(user, request, method):
    from .access import staff_of
    refresh = RefreshToken.for_user(user)
    if staff_of(user):
        FirmAuditLog.objects.create(user=user, action="login", detail={"method": method}, ip_address=_ip(request))
    return Response({"success": True, "message": "Login lykkedes", "data": {
        "user": _user_dict(user),
        "token": str(refresh.access_token),
        "refreshToken": str(refresh),
        "mfa_enabled": mfa.has_mfa(user),
        "mfa_setup_required": mfa.mfa_required_for(user) and not mfa.has_mfa(user),
    }})


def _check_password(user, password):
    stored = user.password or ""
    if stored.startswith(("$2b$", "$2a$")):
        return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    return user.check_password(password)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return _err("Brugernavn og adgangskode skal udfyldes")
    user = _find_login_user(username)
    if user is None or not user.is_active or not _check_password(user, password):
        return _err("Forkert brugernavn eller adgangskode", status.HTTP_401_UNAUTHORIZED)
    if mfa.has_mfa(user):
        return Response({"success": True, "data": {"mfa_required": True, "mfa_token": mfa.make_login_token(user)}})
    return _tokens(user, request, "password")


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def mfa_verify(request):
    user = mfa.user_from_login_token(request.data.get("mfa_token", ""))
    if user is None:
        return _err("Login er udløbet. Start forfra.", status.HTTP_401_UNAUTHORIZED)
    device = mfa.device_of(user)
    if device is None or not device.is_confirmed or not mfa.verify_code(device, request.data.get("code")):
        return _err("Forkert kode", status.HTTP_401_UNAUTHORIZED)
    return _tokens(user, request, "password+totp")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mfa_status(request):
    return Response({"success": True, "data": {
        "enabled": mfa.has_mfa(request.user),
        "required": mfa.mfa_required_for(request.user),
        "recovery_codes_left": len(mfa.device_of(request.user).recovery_codes) if mfa.has_mfa(request.user) else 0,
    }})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_setup(request):
    if mfa.has_mfa(request.user):
        return _err("To-faktor er allerede slået til. Slå det fra først for at skifte app.")
    return Response({"success": True, "data": mfa.start_setup(request.user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_confirm(request):
    codes = mfa.confirm_setup(request.user, request.data.get("code"))
    if codes is None:
        return _err("Koden passer ikke. Tjek at telefonens ur er korrekt, og prøv igen.")
    FirmAuditLog.objects.create(user=request.user, action="mfa_enabled", ip_address=_ip(request))
    return Response({"success": True, "message": "To-faktor er slået til",
                     "data": {"recovery_codes": codes}})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_disable(request):
    device = mfa.device_of(request.user)
    if device is None or not device.is_confirmed:
        return _err("To-faktor er ikke slået til")
    if mfa.mfa_required_for(request.user):
        return _err("Medarbejdere i revisorhuset skal have to-faktor. Opsæt en ny app i stedet.",
                    status.HTTP_403_FORBIDDEN)
    if not _check_password(request.user, request.data.get("password", "")) or \
            not mfa.verify_code(device, request.data.get("code")):
        return _err("Forkert adgangskode eller kode", status.HTTP_401_UNAUTHORIZED)
    device.delete()
    FirmAuditLog.objects.create(user=request.user, action="mfa_disabled", ip_address=_ip(request))
    return Response({"success": True, "message": "To-faktor er slået fra"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    if not _check_password(user, request.data.get("current_password", "")):
        return _err("Den nuværende adgangskode er forkert", status.HTTP_401_UNAUTHORIZED)
    new = request.data.get("new_password", "")
    try:
        validate_password(new, user)
    except ValidationError as e:
        return _err(" ".join(e.messages))
    user.set_password(new)
    user.save()
    return Response({"success": True, "message": "Adgangskoden er skiftet"})
