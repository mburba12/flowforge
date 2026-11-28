"""Account security switches. Each is "on", "off", or "" (= its production default)."""

from flowforge.core.config import settings


def _switch(value: str, production_default: bool) -> bool:
    choice = value.strip().lower()
    if choice in {"on", "true", "1", "yes"}:
        return True
    if choice in {"off", "false", "0", "no"}:
        return False
    return production_default if settings.env == "production" else not production_default


def owner_mfa_required() -> bool:
    """People who manage users or billing must use two-step sign-in (on in production)."""
    return _switch(settings.require_owner_mfa, True)


def verified_email_required() -> bool:
    """Adding a card, connecting a bank and inviting people need a verified email."""
    return _switch(settings.require_verified_email, True)


def bootstrap_allowed() -> bool:
    """The old open "create a workspace with any address" endpoint (tests only)."""
    return _switch(settings.allow_bootstrap, False)


# Holders of any of these must set up two-step sign-in when owner_mfa_required().
MFA_REQUIRED_FOR = {"users.manage", "roles.manage", "account.billing.manage"}
ENROLLMENT_MARKER = "mfa.enrollment_required"
# What someone who still has to set up two-step sign-in may do.
ENROLLMENT_ALLOWED_PATHS = (
    "/api/v1/me",
    "/api/v1/me/permissions",
    "/api/v1/me/preferences",
    "/api/v1/me/security",
    "/api/v1/me/mfa/",
    "/api/v1/me/email/",
    "/api/v1/auth/logout",
)


def enrollment_allows(path: str) -> bool:
    return any(
        path == p or (p.endswith("/") and path.startswith(p)) for p in ENROLLMENT_ALLOWED_PATHS
    )
