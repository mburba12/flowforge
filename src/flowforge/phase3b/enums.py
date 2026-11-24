from enum import StrEnum


class OrderStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    CREDIT_HOLD = "credit_hold"
    RESERVED = "reserved"
    PARTIALLY_SHIPPED = "partially_shipped"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MovementType(StrEnum):
    OPENING = "opening_balance"
    PURCHASE_RECEIPT = "purchase_receipt"
    SALES_ISSUE = "sales_issue"
    ADJUSTMENT_IN = "adjustment_in"
    ADJUSTMENT_OUT = "adjustment_out"
    CUSTOMER_RETURN = "customer_return"


class ARStatus(StrEnum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOIDED = "voided"
