import hashlib
import re
import unicodedata
from urllib.parse import urlparse


def _text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"\s+", " ", normalized)


def normalize_name(value: str) -> str:
    return re.sub(r"[^\w ]+", "", _text(value)).strip()


def normalize_email(value: str) -> str:
    return _text(value).replace(" ", "")


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D+", "", value)
    return digits[-15:]


def normalize_domain(value: str) -> str:
    candidate = value if "://" in value else f"https://{value}"
    return (urlparse(candidate).hostname or "").casefold().removeprefix("www.")


def normalize_address(value: str) -> str:
    return re.sub(r"[^\w ]+", "", _text(value)).strip()


def normalize_sku(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", unicodedata.normalize("NFKC", value).upper())


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_identity_fingerprint(*parts: str) -> str:
    return sha256_text("|".join(_text(part) for part in parts if part))
