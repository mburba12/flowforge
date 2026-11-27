from dataclasses import dataclass

@dataclass(frozen=True)
class FinanceGate:
    journals_balanced: bool
    subledgers_reconciled: bool
    bank_reconciled: bool
    close_exceptions: int

    def passed(self) -> bool:
        return (
            self.journals_balanced
            and self.subledgers_reconciled
            and self.bank_reconciled
            and self.close_exceptions == 0
        )
