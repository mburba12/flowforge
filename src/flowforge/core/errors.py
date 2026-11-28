"""Business-rule refusals raised by FlowForge services.

They subclass PermissionError so existing callers that catch it keep working, but
they are FlowForge exception classes: main.register_domain_errors maps them to
their status_code instead of a server error.
"""


class RuleViolation(PermissionError):
    """An action the business rules do not allow right now (HTTP 409)."""

    status_code = 409


class AccessDenied(RuleViolation):
    """The caller may not perform this action (HTTP 403)."""

    status_code = 403
