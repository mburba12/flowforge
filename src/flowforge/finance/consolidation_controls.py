from decimal import Decimal


def eliminate(intercompany_receivable: Decimal, intercompany_payable: Decimal) -> Decimal:
    variance = intercompany_receivable + intercompany_payable
    if variance != 0:
        raise ValueError("Intercompany balances do not eliminate")
    return variance
