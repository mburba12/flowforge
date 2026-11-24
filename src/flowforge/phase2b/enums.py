from enum import StrEnum


class AccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalance(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class JournalStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"
    REVERSED = "reversed"
    VOIDED = "voided"


class PeriodStatus(StrEnum):
    FUTURE = "future"
    OPEN = "open"
    CLOSED = "closed"
    LOCKED = "locked"
