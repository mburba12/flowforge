from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductAccess:
    permissions: frozenset[str]
    entitlements: frozenset[str]


def authorize(access: ProductAccess, permission: str, module: str) -> None:
    if permission not in access.permissions:
        raise PermissionError(f"Missing permission: {permission}")
    if module not in access.entitlements:
        raise PermissionError(f"Module not entitled: {module}")


def safe_telemetry_dimensions(values: dict[str, object]) -> dict[str, object]:
    forbidden = ("password", "token", "ssn", "bank_account", "tax_id", "document_text")
    if any(any(word in key.casefold() for word in forbidden) for key in values):
        raise ValueError("Sensitive telemetry key")
    return values
