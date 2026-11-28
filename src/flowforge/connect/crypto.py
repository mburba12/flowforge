"""Encryption of stored connection credentials (AES-256-GCM).

Bank access tokens, payroll OAuth tokens and carrier API secrets are stored only in
encrypted form. The key comes from FLOWFORGE_CREDENTIALS_KEY (32 bytes, base64); when it
is unset, a key is derived from the JWT secret. Keys and formats: flowforge.core.crypto.
"""

import json
from typing import Any

from flowforge.core.crypto import decrypt, encrypt

__all__ = ["decrypt", "decrypt_json", "encrypt", "encrypt_json", "mask"]


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
