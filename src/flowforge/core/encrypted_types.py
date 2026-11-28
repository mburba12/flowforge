"""Column types that encrypt on write and decrypt on read (flowforge.core.crypto).

Values stored before encryption was switched on are read as they are and get encrypted
by `python -m flowforge.security.reencrypt` (or the next time the row is saved).
The column name is the authenticated context, so a value moved to another column fails.
"""

from typing import Any

from sqlalchemy import LargeBinary, String
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from flowforge.core import crypto


class EncryptedText(TypeDecorator[str]):
    impl = String
    cache_ok = True

    def __init__(self, context: str, length: int = 1000) -> None:
        super().__init__(length)
        self.context = context

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str | None:
        if value is None or crypto.is_encrypted(value):
            return value
        return crypto.encrypt(value, self.context)

    def process_result_value(self, value: Any, dialect: Dialect) -> str | None:
        if value is None or not crypto.is_encrypted(value):
            return value
        return crypto.decrypt(value, self.context)


class EncryptedBytes(TypeDecorator[bytes]):
    impl = LargeBinary
    cache_ok = True

    def __init__(self, context: str) -> None:
        super().__init__()
        self.context = context

    def process_bind_param(self, value: bytes | None, dialect: Dialect) -> bytes | None:
        if value is None or crypto.bytes_encrypted(value):
            return value
        return crypto.encrypt_bytes(value, self.context)

    def process_result_value(self, value: Any, dialect: Dialect) -> bytes | None:
        if value is None:
            return None
        return crypto.decrypt_bytes(bytes(value), self.context)


# Every encrypted column (table, column, context, kind) for the re-encryption tool.
ENCRYPTED_COLUMNS: list[tuple[str, str, str, str]] = [
    ("worker_bank_accounts", "account_token", "worker_bank_accounts.account_token", "text"),
    ("worker_bank_accounts", "routing_token", "worker_bank_accounts.routing_token", "text"),
    ("tax_registrations", "registration_token", "tax_registrations.registration_token", "text"),
    ("attachments", "content", "attachments.content", "bytes"),
    ("user_mfa", "secret", "user_mfa.secret", "text"),
]
