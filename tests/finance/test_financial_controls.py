from dataclasses import dataclass
from decimal import Decimal

import pytest

from flowforge.finance.controls import (
    AP_TRANSITIONS,
    FinancialControlError,
    assert_balanced,
    assert_nonnegative,
    assert_transition,
)


@dataclass
class L:
    debit: Decimal
    credit: Decimal


def test_balance_control():
    assert_balanced([L(Decimal("10"), Decimal("0")), L(Decimal("0"), Decimal("10"))])


def test_unbalanced_rejected():
    with pytest.raises(FinancialControlError):
        assert_balanced([L(Decimal("10"), Decimal("0"))])


def test_negative_rejected():
    with pytest.raises(FinancialControlError):
        assert_nonnegative(Decimal("-1"))


def test_state_transition_rejected():
    with pytest.raises(FinancialControlError):
        assert_transition("draft", "paid", AP_TRANSITIONS)
