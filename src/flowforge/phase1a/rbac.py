from dataclasses import dataclass, field

from .errors import AuthorizationError


@dataclass(slots=True)
class Role:
    name: str
    permissions: set[str] = field(default_factory=set)
    system: bool = False


@dataclass(slots=True)
class Principal:
    roles: list[Role]

    @property
    def permissions(self) -> set[str]:
        return set().union(*(r.permissions for r in self.roles)) if self.roles else set()


def require_permission(principal: Principal, permission: str) -> None:
    if permission not in principal.permissions:
        raise AuthorizationError(f"Missing permission: {permission}")


def validate_separation(principal: Principal, forbidden_pairs: set[tuple[str, str]]) -> None:
    p = principal.permissions
    for a, b in forbidden_pairs:
        if a in p and b in p:
            raise AuthorizationError(f"Separation-of-duties conflict: {a} + {b}")
