from dataclasses import dataclass
from enum import StrEnum


class ActionState(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FAILED = "failed"
    MANUAL_INTERVENTION = "manual_intervention"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    ROLLED_BACK = "rolled_back"


TRANSITIONS = {
    ActionState.DRAFT: {ActionState.VALIDATED, ActionState.REJECTED},
    ActionState.VALIDATED: {ActionState.AWAITING_APPROVAL, ActionState.REJECTED},
    ActionState.AWAITING_APPROVAL: {
        ActionState.APPROVED,
        ActionState.REJECTED,
        ActionState.EXPIRED,
    },
    ActionState.APPROVED: {ActionState.SCHEDULED, ActionState.EXECUTING},
    ActionState.SCHEDULED: {ActionState.EXECUTING, ActionState.EXPIRED},
    ActionState.EXECUTING: {
        ActionState.COMPLETED,
        ActionState.FAILED,
        ActionState.MANUAL_INTERVENTION,
    },
    ActionState.FAILED: {ActionState.COMPENSATING, ActionState.MANUAL_INTERVENTION},
    ActionState.COMPENSATING: {
        ActionState.COMPENSATED,
        ActionState.MANUAL_INTERVENTION,
    },
    ActionState.COMPLETED: {ActionState.ROLLED_BACK},
}


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    creator_id: str
    approver_id: str
    approved: bool


def transition(current: ActionState, target: ActionState) -> ActionState:
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {target}")
    return target


def enforce_separation(decision: ApprovalDecision) -> None:
    if decision.creator_id == decision.approver_id:
        raise ValueError("Creator cannot approve own action")


def deterministic_idempotency(tenant_id: str, action_type: str, natural_key: str) -> str:
    return f"{tenant_id}:{action_type}:{natural_key}"
