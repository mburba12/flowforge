from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum


class ActivationLevel(IntEnum):
    DISABLED = 0
    PRODUCTION_READ = 1
    REVERSIBLE_WRITE = 2
    ACCOUNTING_DRAFT = 3
    LOGISTICS_ACTION = 4
    WORKFORCE_DRAFT = 5
    HIGH_RISK = 6


@dataclass(frozen=True, slots=True)
class ActivationPolicy:
    tenant_id: str
    provider: str
    level: ActivationLevel
    transaction_limit: Decimal
    two_person_approval: bool
    trusted_beneficiary_required: bool
    step_up_authentication: bool


def authorize_execution(
    policy: ActivationPolicy,
    required: ActivationLevel,
    amount: Decimal,
    approver_count: int,
    trusted_beneficiary: bool,
    step_up_complete: bool,
) -> None:
    if policy.level < required:
        raise ValueError("Activation level insufficient")
    if amount > policy.transaction_limit:
        raise ValueError("Transaction limit exceeded")
    if required == ActivationLevel.HIGH_RISK:
        if not policy.two_person_approval or approver_count < 2:
            raise ValueError("Two-person approval required")
        if policy.trusted_beneficiary_required and not trusted_beneficiary:
            raise ValueError("Trusted beneficiary required")
        if policy.step_up_authentication and not step_up_complete:
            raise ValueError("Step-up authentication required")
