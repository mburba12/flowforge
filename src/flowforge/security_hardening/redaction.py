import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {
    "access_token",
    "refresh_token",
    "authorization_code",
    "account_number",
    "routing_number",
    "tax_id",
    "ssn",
    "webhook_secret",
    "client_secret",
    "password",
}
TOKEN_PATTERN = re.compile(r"(?i)(bearer\s+)[a-z0-9._~+/-]+=*")


def redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return TOKEN_PATTERN.sub(r"\1[REDACTED]", value)
    return value
