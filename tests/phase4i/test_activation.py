from decimal import Decimal

import pytest

from flowforge.phase4i.activation import (
    ActivationLevel,
    ActivationPolicy,
    authorize_execution,
)


def policy(level: ActivationLevel) -> ActivationPolicy:
    return ActivationPolicy("t", "p", level, Decimal(1000), True, True, True)


def test_read() -> None:
    authorize_execution(
        policy(ActivationLevel.PRODUCTION_READ),
        ActivationLevel.PRODUCTION_READ,
        Decimal(0),
        0,
        False,
        False,
    )


def test_high_risk() -> None:
    authorize_execution(
        policy(ActivationLevel.HIGH_RISK),
        ActivationLevel.HIGH_RISK,
        Decimal(100),
        2,
        True,
        True,
    )


def test_limit() -> None:
    with pytest.raises(ValueError):
        authorize_execution(
            policy(ActivationLevel.HIGH_RISK),
            ActivationLevel.HIGH_RISK,
            Decimal(1001),
            2,
            True,
            True,
        )


def test_approval() -> None:
    with pytest.raises(ValueError):
        authorize_execution(
            policy(ActivationLevel.HIGH_RISK),
            ActivationLevel.HIGH_RISK,
            Decimal(100),
            1,
            True,
            True,
        )
