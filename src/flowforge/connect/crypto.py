"""Encryption of stored connection credentials (AES-256-GCM).

Bank access tokens, payroll OAuth tokens and carrier API secrets are stored only in
encrypted form. The key comes from FLOWFORGE_CREDENTIALS_KEY (32 bytes, base64); when it
is unset, a key is derived from the JWT secret with HKDF so a deployment works without
extra configuration. Ciphertexts carry a version prefix so the key can be rotated.
"""

import base64
import json
import os
from functools import lru_cache
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from flowforge.core.config import settings

_PREFIX = "ffc1:"


@lru_cache(maxsize=1)
def _key() -> bytes:
    if settings.credentials_key:
        key = base64.b64decode(settings.credentials_key)
        if len(key) != 32:
            raise RuntimeError("FLOWFORGE_CREDENTIALS_KEY must be 32 bytes, base64-encoded")
        return key
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=b"flowforge", info=b"connection-credentials"
    ).derive(settings.jwt_secret.encode())


def encrypt(plaintext: str, context: str) -> str:
    """Encrypt `plaintext`; `context` (e.g. the tenant id) is authenticated, not stored."""
    nonce = os.urandom(12)
    sealed = AESGCM(_key()).encrypt(nonce, plaintext.encode(), context.encode())
    return _PREFIX + base64.urlsafe_b64encode(nonce + sealed).decode()


def decrypt(ciphertext: str, context: str) -> str:
    if not ciphertext.startswith(_PREFIX):
        raise ValueError("Stored credential is not readable; reconnect the account")
    raw = base64.urlsafe_b64decode(ciphertext[len(_PREFIX) :])
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], context.encode()).decode()


def encrypt_json(value: dict[str, Any], context: str) -> str:
    return encrypt(json.dumps(value, separators=(",", ":")), context)


def decrypt_json(ciphertext: str, context: str) -> dict[str, Any]:
    value = json.loads(decrypt(ciphertext, context))
    if not isinstance(value, dict):
        raise ValueError("Stored credential is not readable; reconnect the account")
    return value


def mask(value: str, keep: int = 4) -> str:
    value = value.strip()
    return ("•" * max(0, min(len(value) - keep, 6))) + value[-keep:] if value else ""
