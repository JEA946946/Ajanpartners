"""To-faktor-login med TOTP (Google Authenticator, Microsoft Authenticator m.fl.).

Login i to trin: /auth/login svarer `mfa_required` og et kortlivet `mfa_token`
(signeret, 5 minutter), og /auth/mfa/verify bytter token + kode til JWT.
"""

import base64
import hashlib
import io
import secrets
import time

import pyotp
from django.conf import settings
from django.core import signing
from django.utils import timezone

from payroll.crypto import decrypt, encrypt

from .models import MFADevice

ISSUER = "Ajan Partners Bogføring"
MFA_TOKEN_SALT = "tenancy.mfa.login"
MFA_TOKEN_MAX_AGE = 300


def _hash(code):
    return hashlib.sha256(code.replace("-", "").strip().lower().encode()).hexdigest()


def device_of(user):
    return MFADevice.objects.filter(user=user).first()


def has_mfa(user):
    d = device_of(user)
    return bool(d and d.is_confirmed)


def mfa_required_for(user):
    """Medarbejdere i revisorhuset skal have MFA (settings.FIRM_MFA_REQUIRED)."""
    from .access import staff_of
    return bool(getattr(settings, "FIRM_MFA_REQUIRED", True) and staff_of(user))


def start_setup(user):
    """Ny (ubekræftet) hemmelighed. Returnerer secret, otpauth-URI og QR som data-URL."""
    secret = pyotp.random_base32()
    MFADevice.objects.update_or_create(user=user, defaults={
        "secret_encrypted": encrypt(secret), "confirmed_at": None, "recovery_codes": [], "last_used_step": 0})
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email or user.username, issuer_name=ISSUER)
    return {"secret": secret, "otpauth_uri": uri, "qr": _qr_data_url(uri)}


def _qr_data_url(text):
    import qrcode
    img = qrcode.make(text, box_size=6, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def verify_code(device, code):
    """TOTP-kode (±1 tidsvindue, ingen genbrug) eller en gendannelseskode."""
    code = (code or "").strip().replace(" ", "")
    if not code:
        return False
    if code.isdigit() and len(code) == 6:
        totp = pyotp.TOTP(decrypt(device.secret_encrypted))
        now_step = int(time.time()) // totp.interval
        for step in (now_step - 1, now_step, now_step + 1):
            if step <= device.last_used_step:
                continue
            if secrets.compare_digest(totp.generate_otp(step), code):
                device.last_used_step = step
                device.save(update_fields=["last_used_step"])
                return True
        return False
    h = _hash(code)
    if h in device.recovery_codes:
        device.recovery_codes = [c for c in device.recovery_codes if c != h]
        device.save(update_fields=["recovery_codes"])
        return True
    return False


def confirm_setup(user, code):
    """Bekræft med en kode fra appen. Returnerer 10 gendannelseskoder (vises én gang) eller None."""
    device = device_of(user)
    if device is None or not verify_code(device, code):
        return None
    codes = [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(10)]
    device.recovery_codes = [_hash(c) for c in codes]
    device.confirmed_at = timezone.now()
    device.save(update_fields=["recovery_codes", "confirmed_at"])
    return codes


def make_login_token(user):
    return signing.dumps({"uid": user.pk}, salt=MFA_TOKEN_SALT)


def user_from_login_token(token):
    from django.contrib.auth import get_user_model
    try:
        data = signing.loads(token, salt=MFA_TOKEN_SALT, max_age=MFA_TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None
    return get_user_model().objects.filter(pk=data.get("uid"), is_active=True).first()
