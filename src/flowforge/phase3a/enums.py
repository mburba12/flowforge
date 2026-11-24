from enum import StrEnum


class PurchaseOrderStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReceiptStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"


class InvoiceStatus(StrEnum):
    CAPTURED = "captured"
    VALIDATED = "validated"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    POSTED = "posted"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOIDED = "voided"
    ON_HOLD = "on_hold"


class MatchStatus(StrEnum):
    MATCHED = "matched"
    WITHIN_TOLERANCE = "within_tolerance"
    EXCEPTION = "exception"
    MISSING_RECEIPT = "missing_receipt"
    QUANTITY_VARIANCE = "quantity_variance"
    PRICE_VARIANCE = "price_variance"
