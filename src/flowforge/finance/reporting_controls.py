from decimal import Decimal


def trial_balance(debits: list[Decimal], credits: list[Decimal]) -> dict[str, object]:
    d = sum(debits, Decimal("0"))
    c = sum(credits, Decimal("0"))
    return {"debits": d, "credits": c, "balanced": d == c}


def balance_sheet_balanced(assets: Decimal, liabilities: Decimal, equity: Decimal) -> bool:
    return assets == liabilities + equity
