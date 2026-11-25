import pytest

from flowforge.phase4g.workflow import (
    ActionState,
    ApprovalDecision,
    deterministic_idempotency,
    enforce_separation,
    transition,
)


def test_transition() -> None:
    assert transition(ActionState.DRAFT, ActionState.VALIDATED) == ActionState.VALIDATED


def test_invalid_transition() -> None:
    with pytest.raises(ValueError):
        transition(ActionState.DRAFT, ActionState.COMPLETED)


def test_separation() -> None:
    with pytest.raises(ValueError):
        enforce_separation(ApprovalDecision("u", "u", True))


def test_idempotency() -> None:
    assert deterministic_idempotency("t", "bill", "1") == "t:bill:1"
