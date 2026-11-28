"""Authenticator-app codes (TOTP, RFC 6238: SHA-1, 30-second steps, 6 digits) and recovery codes."""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

STEP_SECONDS = 30
DIGITS = 6
WINDOW = 1  # accept the previous and next step for clock drift


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _key(secret: str) -> bytes:
    padded = secret.upper() + "=" * (-len(secret) % 8)
    return base64.b32decode(padded)


def code_at(secret: str, step: int) -> str:
    digest = hmac.new(_key(secret), struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(number % 10**DIGITS).zfill(DIGITS)


def current_step(now: float | None = None) -> int:
    return int((now if now is not None else time.time()) // STEP_SECONDS)


def verify(secret: str, code: str, last_step: int, now: float | None = None) -> int | None:
    """The time step the code belongs to, or None. A step at or before last_step is
    refused, so a code cannot be used twice."""
    code = "".join(ch for ch in code if ch.isdigit())
    if len(code) != DIGITS:
        return None
    step = current_step(now)
    for candidate in range(step - WINDOW, step + WINDOW + 1):
        if candidate > last_step and hmac.compare_digest(code_at(secret, candidate), code):
            return candidate
    return None


def otpauth_uri(secret: str, account: str, issuer: str = "Krov WorkAgent") -> str:
    label = quote(f"{issuer}:{account}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&digits={DIGITS}&period={STEP_SECONDS}"


def new_recovery_codes(count: int = 10) -> list[str]:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    codes = []
    for _ in range(count):
        raw = "".join(secrets.choice(alphabet) for _ in range(8))
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def hash_code(code: str) -> str:
    normalized = "".join(ch for ch in code.upper() if ch.isalnum())
    return hashlib.sha256(b"krov-recovery:" + normalized.encode()).hexdigest()
