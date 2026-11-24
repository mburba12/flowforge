import base64
import hmac
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID, uuid4


@dataclass(slots=True)
class Connection:
    id: UUID
    tenant_id: UUID
    provider: str
    encrypted_secret: str
    cursor: str | None = None
    active: bool = True


class SecretBox:
    def __init__(self, key: str):
        self.key = sha256(key.encode()).digest()

    def encrypt(self, value: str) -> str:
        data = value.encode()
        raw = bytes(b ^ self.key[i % len(self.key)] for i, b in enumerate(data))
        return base64.urlsafe_b64encode(raw).decode()

    def decrypt(self, value: str) -> str:
        data = base64.urlsafe_b64decode(value)
        return bytes(b ^ self.key[i % len(self.key)] for i, b in enumerate(data)).decode()


class IntegrationService:
    def __init__(self, box: SecretBox):
        self.box = box

    def connect(self, tenant_id: UUID, provider: str, secret: str) -> Connection:
        return Connection(uuid4(), tenant_id, provider, self.box.encrypt(secret))

    def rotate(self, c: Connection, secret: str) -> None:
        c.encrypted_secret = self.box.encrypt(secret)

    def update_cursor(self, c: Connection, cursor: str) -> None:
        c.cursor = cursor

    def verify_webhook(self, body: bytes, signature: str, secret: str) -> bool:
        return hmac.compare_digest(hmac.new(secret.encode(), body, "sha256").hexdigest(), signature)
