"""Two-person approval with designated exceptions.

By default the person who creates a journal, purchase order, payroll run, tax return,
close run or merge proposal cannot approve it. Users holding SELF_APPROVE (the Owner
role, and anyone given the "Approve own work" role or a custom role with it) may.

enforce() in flowforge.platform.authorization records the caller's permissions for the
current request; the approval checks read them through may_approve_own().
"""

from contextvars import ContextVar

SELF_APPROVE = "approvals.self_approve"
SELF_APPROVE_ROLE = "Approve own work"

_permissions: ContextVar[frozenset[str]] = ContextVar("ff_request_permissions", default=frozenset())


def set_request_permissions(codes: set[str] | frozenset[str]) -> None:
    _permissions.set(frozenset(codes))


def may_approve_own() -> bool:
    return SELF_APPROVE in _permissions.get()


def blocks_self_approval(created_by: object, approver: object) -> bool:
    """True when the creator is approving their own work without the exception."""
    return created_by is not None and created_by == approver and not may_approve_own()
