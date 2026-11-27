from decimal import Decimal

from flowforge.finance.ap_controls import assert_match
from flowforge.finance.ar_controls import allocate
from flowforge.finance.asset_controls import straight_line
from flowforge.finance.banking_controls import transaction_fingerprint
from flowforge.finance.consolidation_controls import eliminate
from flowforge.finance.gl_close import validate_close
from flowforge.finance.integrated_controls import FinanceGate
from flowforge.finance.reporting_controls import balance_sheet_balanced


def test_controls():
    validate_close("P1", Decimal("10"), Decimal("10"), 0)
    assert_match(Decimal("10"), Decimal("9"), Decimal("1"))
    assert allocate(Decimal("10"), Decimal("4")) == (Decimal("6"), Decimal("0"))
    assert straight_line(Decimal("120"), Decimal("0"), 12) == Decimal("10.00")
    assert transaction_fingerprint("a", "d", "1", "x") == transaction_fingerprint(
        "a", "d", "1", "x"
    )
    assert eliminate(Decimal("5"), Decimal("-5")) == 0
    assert balance_sheet_balanced(Decimal("10"), Decimal("4"), Decimal("6"))
    assert FinanceGate(True, True, True, 0).passed()
