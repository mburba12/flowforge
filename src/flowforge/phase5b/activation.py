from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum, StrEnum


class ActivationLevel(IntEnum):
    DISABLED = 0
    PRODUCTION_READ = 1
    REVERSIBLE_WRITE = 2
    ACCOUNTING_DRAFT = 3
    LOGISTICS_ACTION = 4
    WORKFORCE_DRAFT = 5
    HIGH_RISK = 6


class Provider(StrEnum):
    QUICKBOOKS = "quickbooks_online"
    STRIPE = "stripe"
    SHOPIFY = "shopify"
    UPS = "ups"
    ADP = "adp_workforce_now"
    SALESFORCE = "salesforce_sales_cloud"
    TEAMS = "microsoft_teams"


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    tenant_id: str
    provider: Provider
    activation_level: ActivationLevel
    amount: Decimal
    transaction_limit: Decimal
    approver_ids: tuple[str, ...]
    creator_id: str
    trusted_beneficiary: bool
    step_up_complete: bool
    simulation_passed: bool
    idempotency_key: str
    incident_locked: bool


def authorize(ctx: ExecutionContext, required: ActivationLevel) -> None:
    if ctx.incident_locked:
        raise PermissionError("Tenant is incident locked")
    if ctx.activation_level < required:
        raise PermissionError("Activation level insufficient")
    if not ctx.idempotency_key:
        raise ValueError("Idempotency key is required")
    if not ctx.simulation_passed:
        raise PermissionError("Simulation must pass")
    if ctx.amount > ctx.transaction_limit:
        raise PermissionError("Transaction limit exceeded")
    if required == ActivationLevel.HIGH_RISK:
        independent = {user for user in ctx.approver_ids if user != ctx.creator_id}
        if len(independent) < 2:
            raise PermissionError("Two independent approvers required")
        if not ctx.trusted_beneficiary:
            raise PermissionError("Trusted beneficiary required")
        if not ctx.step_up_complete:
            raise PermissionError("Step-up authentication required")
