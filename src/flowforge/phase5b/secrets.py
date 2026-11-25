from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class SecretReference:
    vault_uri: str
    secret_name: str
    version: str | None = None

    def validate(self) -> None:
        parsed = urlparse(self.vault_uri)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not parsed.hostname.endswith(".vault.azure.net")
        ):
            raise ValueError("Azure Key Vault HTTPS URI required")
        if not self.secret_name or any(ch.isspace() for ch in self.secret_name):
            raise ValueError("Valid secret name required")


def reject_raw_credentials(configuration: dict[str, object]) -> None:
    forbidden = (
        "password",
        "client_secret",
        "api_key",
        "private_key",
        "access_token",
        "refresh_token",
    )
    for key, value in configuration.items():
        if any(token in key.casefold() for token in forbidden) and value:
            raise ValueError(f"Raw credential prohibited: {key}")
