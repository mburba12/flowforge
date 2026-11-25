from decimal import Decimal

import pytest

from flowforge.phase5b.activation import ActivationLevel, ExecutionContext, Provider, authorize


def context(**changes):
    values = dict(
        tenant_id="t",
        provider=Provider.STRIPE,
        activation_level=ActivationLevel.HIGH_RISK,
        amount=Decimal("100"),
        transaction_limit=Decimal("1000"),
        approver_ids=("a", "b"),
        creator_id="c",
        trusted_beneficiary=True,
        step_up_complete=True,
        simulation_passed=True,
        idempotency_key="key",
        incident_locked=False,
    )
    values.update(changes)
    return ExecutionContext(**values)


def test_authorized():
    authorize(context(), ActivationLevel.HIGH_RISK)


def test_lockout():
    with pytest.raises(PermissionError):
        authorize(context(incident_locked=True), ActivationLevel.PRODUCTION_READ)


def test_two_approvers():
    with pytest.raises(PermissionError):
        authorize(context(approver_ids=("a",)), ActivationLevel.HIGH_RISK)


def test_limit():
    with pytest.raises(PermissionError):
        authorize(context(amount=Decimal("1001")), ActivationLevel.HIGH_RISK)
