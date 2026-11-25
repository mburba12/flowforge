from dataclasses import dataclass
from typing import Protocol


class KeyWrappingProvider(Protocol):
    def encrypt(self, plaintext: str) -> tuple[str, str, str]: ...
    def decrypt(self, ciphertext: str, key_id: str, key_version: str) -> str: ...


@dataclass(frozen=True, slots=True)
class EncryptedValue:
    ciphertext: str
    key_id: str
    key_version: str


class EnvelopeEncryptor:
    def __init__(self, provider: KeyWrappingProvider):
        self.provider = provider

    def encrypt(self, plaintext: str) -> EncryptedValue:
        if not plaintext:
            raise ValueError("Sensitive plaintext cannot be empty")
        ciphertext, key_id, version = self.provider.encrypt(plaintext)
        return EncryptedValue(ciphertext, key_id, version)

    def decrypt(self, value: EncryptedValue) -> str:
        return self.provider.decrypt(value.ciphertext, value.key_id, value.key_version)
