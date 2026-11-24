import re
import unicodedata


def normalize_name(value: str) -> str:
    return re.sub(
        r"[^a-z0-9 ]",
        "",
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower(),
    ).strip()


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value)


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())
