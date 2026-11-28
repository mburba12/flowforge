"""Encryption at rest for sensitive values and files (AES-256-GCM, rotatable keys).

Keys
* The current key is FLOWFORGE_CREDENTIALS_KEY (32 random bytes, base64). Until one is
  set, a key derived from the JWT secret is used (the legacy behaviour).
* Older keys stay readable: FLOWFORGE_CREDENTIALS_KEY_PREVIOUS (comma-separated, base64)
  and always the key derived from the current JWT secret. Every value records which key
  sealed it, so `python -m flowforge.security.reencrypt` can move everything to the
  current key; after that, old keys can be dropped and the JWT secret rotated.

Formats
* text: "ffc2:<key id>:<base64 nonce+ciphertext>"; legacy "ffc1:<...>" is still read.
* bytes: b"FFE2" + 4-byte key id + 12-byte nonce + ciphertext.
The `context` (for example "tenant:kind:id" or a column name) is authenticated: a value
copied to another row or column does not decrypt.
"""

import base64
import hashlib
import os
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from flowforge.core.config import settings

TEXT_V1 = "ffc1:"
TEXT_V2 = "ffc2:"
BYTES_V2 = b"FFE2"


def _derived_from_jwt() -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=b"flowforge", info=b"connection-credentials"
    ).derive(settings.jwt_secret.encode())


def _decode_key(value: str, name: str) -> bytes:
    key = base64.b64decode(value.strip())
    if len(key) != 32:
        raise RuntimeError(f"{name} must be 32 bytes, base64-encoded")
    return key


def key_id(key: bytes) -> bytes:
    return hashlib.sha256(b"krov-key-id" + key).digest()[:4]


@lru_cache(maxsize=1)
def _keyring() -> tuple[bytes, dict[bytes, bytes]]:
    """(current key, {key id: key} of every key that can decrypt)."""
    current = (
        _decode_key(settings.credentials_key, "FLOWFORGE_CREDENTIALS_KEY")
        if settings.credentials_key
        else _derived_from_jwt()
    )
    keys = [current, _derived_from_jwt()]
    for item in (settings.credentials_key_previous or "").split(","):
        if item.strip():
            keys.append(_decode_key(item, "FLOWFORGE_CREDENTIALS_KEY_PREVIOUS"))
    return current, {key_id(k): k for k in keys}


def reset_keys() -> None:
    """Forget cached keys (tests and the re-encryption tool change settings)."""
    _keyring.cache_clear()


def current_key_id() -> bytes:
    return key_id(_keyring()[0])


def uses_dedicated_key() -> bool:
    return bool(settings.credentials_key)


# ------------------------------------------------------------------ text
def encrypt(plaintext: str, context: str) -> str:
    current, _ = _keyring()
    nonce = os.urandom(12)
    sealed = AESGCM(current).encrypt(nonce, plaintext.encode(), context.encode())
    return f"{TEXT_V2}{key_id(current).hex()}:{base64.urlsafe_b64encode(nonce + sealed).decode()}"


def is_encrypted(value: str | None) -> bool:
    return bool(value) and (value.startswith(TEXT_V2) or value.startswith(TEXT_V1))  # type: ignore[union-attr]


def needs_reencryption(value: str | None) -> bool:
    """Stored in plain text, in the legacy format, or under a key that is not current."""
    if not value:
        return False
    if value.startswith(TEXT_V2):
        return value[len(TEXT_V2) : len(TEXT_V2) + 8] != current_key_id().hex()
    return True


def decrypt(ciphertext: str, context: str) -> str:
    _, keys = _keyring()
    if ciphertext.startswith(TEXT_V2):
        kid_hex, _, body = ciphertext[len(TEXT_V2) :].partition(":")
        key = keys.get(bytes.fromhex(kid_hex)) if len(kid_hex) == 8 else None
        if key is None:
            raise ValueError("Stored value was sealed with a key this server does not have")
        raw = base64.urlsafe_b64decode(body)
        return AESGCM(key).decrypt(raw[:12], raw[12:], context.encode()).decode()
    if ciphertext.startswith(TEXT_V1):  # legacy: no key id, try every key
        raw = base64.urlsafe_b64decode(ciphertext[len(TEXT_V1) :])
        for key in keys.values():
            try:
                return AESGCM(key).decrypt(raw[:12], raw[12:], context.encode()).decode()
            except Exception:  # noqa: BLE001,S112 - try the next key
                continue
        raise ValueError("Stored credential is not readable; reconnect the account")
    raise ValueError("Stored credential is not readable; reconnect the account")


# ------------------------------------------------------------------ bytes
def encrypt_bytes(data: bytes, context: str) -> bytes:
    current, _ = _keyring()
    nonce = os.urandom(12)
    return (
        BYTES_V2 + key_id(current) + nonce + AESGCM(current).encrypt(nonce, data, context.encode())
    )


def bytes_encrypted(data: bytes | None) -> bool:
    return bool(data) and data[:4] == BYTES_V2  # type: ignore[index]


def bytes_need_reencryption(data: bytes | None) -> bool:
    if not data:
        return False
    return not bytes_encrypted(data) or data[4:8] != current_key_id()


def decrypt_bytes(data: bytes, context: str) -> bytes:
    """Decrypt; data stored before encryption was switched on is returned unchanged."""
    if not bytes_encrypted(data):
        return data
    key = _keyring()[1].get(data[4:8])
    if key is None:
        raise ValueError("Stored file was sealed with a key this server does not have")
    return AESGCM(key).decrypt(data[8:20], data[20:], context.encode())
