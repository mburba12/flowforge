import hashlib


def transaction_fingerprint(account_id: str, posted_date: str, amount: str, memo: str) -> str:
    return hashlib.sha256(
        f"{account_id}|{posted_date}|{amount}|{memo.strip().lower()}".encode()
    ).hexdigest()


def assert_reconciled(statement: object, ledger: object) -> None:
    if statement != ledger:
        raise ValueError("Bank reconciliation is not balanced")
