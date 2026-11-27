"""AR release workflow: customer -> order -> credit -> reserve -> ship/invoice -> receipt."""

from decimal import Decimal
from uuid import uuid4

from .conftest import IN_PERIOD, Harness


async def _customer(h: Harness, name: str, credit_limit: str) -> str:
    party = await h.organization(name)
    customer = await h.post(
        "/api/v3b/customers",
        json={
            "party_id": party,
            "default_currency": "USD",
            "ar_account_id": h.accounts["ar"],
            "revenue_account_id": h.accounts["revenue"],
            "credit_limit": credit_limit,
        },
    )
    return str(customer["id"])


async def _stocked_product(h: Harness, on_hand: str = "50") -> tuple[str, str, str]:
    warehouse = await h.post("/api/v3b/warehouses", json={"code": "MAIN", "name": "Main"})
    location = await h.post(
        "/api/v3b/locations", json={"warehouse_id": warehouse["id"], "code": "A-01"}
    )
    product = await h.post(
        "/api/v3b/products",
        json={
            "sku": "SKU-100",
            "name": "Gadget",
            "base_uom": "EA",
            "sales_price": "10.00",
            "standard_cost": "6.00",
            "inventory_account_id": h.accounts["inventory"],
            "cogs_account_id": h.accounts["cogs"],
        },
    )
    await h.post(
        "/api/v3b/inventory/adjust",
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "location_id": location["id"],
            "quantity": on_hand,
            "unit_cost": "6.00",
            "idempotency_key": f"init-{uuid4().hex}",
            "accounting": _accounting(h),
        },
    )
    return str(product["id"]), str(warehouse["id"]), str(location["id"])


def _accounting(h: Harness) -> dict[str, str]:
    # Opening stock is valued against equity (opening balance offset).
    return {
        "ledger_id": h.ledger_id,
        "period_id": h.period_id,
        "offset_account_id": h.accounts["equity"],
        "adjustment_date": IN_PERIOD.isoformat(),
    }


async def _order(h: Harness, customer_id: str, product_id: str, qty: str) -> dict[str, str]:
    order: dict[str, str] = await h.post(
        "/api/v3b/orders",
        json={
            "customer_id": customer_id,
            "ledger_id": h.ledger_id,
            "period_id": h.period_id,
            "order_date": IN_PERIOD.isoformat(),
            "lines": [{"product_id": product_id, "quantity": qty, "unit_price": "10.00"}],
        },
    )
    return order


async def _balance(h: Harness, product_id: str) -> tuple[Decimal, Decimal]:
    rows = await h.sql(
        "SELECT on_hand, reserved FROM inventory_balances WHERE product_id = :p", p=product_id
    )
    return Decimal(rows[0][0]), Decimal(rows[0][1])


async def test_ar_order_to_cash(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "Globex Retail Inc", "10000")
    product_id, warehouse_id, location_id = await _stocked_product(h)

    # Inventory idempotency and no negative stock.
    key = f"adj-{uuid4().hex}"
    adjust = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "location_id": location_id,
        "quantity": "0.5",
        "unit_cost": "6.00",
        "idempotency_key": key,
        "accounting": _accounting(h),
    }
    await h.post("/api/v3b/inventory/adjust", json=adjust)
    await h.post("/api/v3b/inventory/adjust", json=adjust, expect=409)
    await h.post(
        "/api/v3b/inventory/adjust",
        json={**adjust, "quantity": "-1000", "idempotency_key": f"neg-{uuid4().hex}"},
        expect=409,
    )
    await h.post(
        "/api/v3b/inventory/adjust",
        json={**adjust, "quantity": "-0.5", "idempotency_key": f"rev-{uuid4().hex}"},
    )
    assert await _balance(h, product_id) == (Decimal("50"), Decimal("0"))

    # Order lifecycle with status enforcement.
    order = await _order(h, customer_id, product_id, "20")
    assert (order["status"], Decimal(order["total"])) == ("approved", Decimal("200.00"))
    order_id = order["id"]
    await h.post(
        f"/api/v3b/orders/{order_id}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": "2026-02-14"},
        expect=409,
    )  # not reserved yet
    reserved = await h.post(f"/api/v3b/orders/{order_id}/reserve")
    assert reserved["status"] == "reserved"
    await h.post(f"/api/v3b/orders/{order_id}/reserve", expect=409)
    assert await _balance(h, product_id) == (Decimal("50"), Decimal("20"))

    too_big = await _order(h, customer_id, product_id, "31")
    await h.post(f"/api/v3b/orders/{too_big['id']}/reserve", expect=409)  # only 30 available

    invoice = await h.post(
        f"/api/v3b/orders/{order_id}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": "2026-02-14"},
    )
    assert Decimal(invoice["total"]) == Decimal("200.00")
    await h.post(
        f"/api/v3b/orders/{order_id}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": "2026-02-14"},
        expect=409,
    )  # shipping twice is rejected
    assert await _balance(h, product_id) == (Decimal("30"), Decimal("0"))
    status = await h.sql("SELECT status FROM sales_orders WHERE id = :o", o=order_id)
    assert status[0][0] == "invoiced"

    await h.assert_ledger_integrity()
    assert await h.account_balance("ar") == Decimal("200.00")
    assert await h.account_balance("revenue") == Decimal("-200.00")
    assert await h.account_balance("cogs") == Decimal("120.00")

    # Receipts: over-allocation rejected, partial then final.
    item = await h.sql(
        "SELECT id, open_amount, status FROM ar_open_items WHERE invoice_id = :i", i=invoice["id"]
    )
    open_item_id = str(item[0][0])
    assert (Decimal(item[0][1]), item[0][2]) == (Decimal("200.00"), "open")

    def receipt(amount: str) -> dict[str, str]:
        return {
            "open_item_id": open_item_id,
            "amount": amount,
            "receipt_date": IN_PERIOD.isoformat(),
            "cash_account_id": h.accounts["cash"],
            "ar_account_id": h.accounts["ar"],
            "ledger_id": h.ledger_id,
            "period_id": h.period_id,
            "currency_code": "USD",
        }

    await h.post("/api/v3b/receipts", json=receipt("200.01"), expect=409)
    await h.post("/api/v3b/receipts", json=receipt("150.00"))
    partial = await h.sql(
        "SELECT open_amount, status FROM ar_open_items WHERE id = :i", i=open_item_id
    )
    assert (Decimal(partial[0][0]), partial[0][1]) == (Decimal("50.00"), "partially_paid")
    await h.post("/api/v3b/receipts", json=receipt("50.00"))
    await h.post("/api/v3b/receipts", json=receipt("0.01"), expect=409)
    paid = await h.sql(
        "SELECT open_amount, status FROM ar_open_items WHERE id = :i", i=open_item_id
    )
    assert (Decimal(paid[0][0]), paid[0][1]) == (Decimal("0.00"), "paid")

    await h.assert_ledger_integrity()
    assert await h.account_balance("ar") == Decimal("0.00")
    assert await h.account_balance("cash") == Decimal("200.00")


async def test_ar_credit_limit_holds_order(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "Tight Credit Co", "100")
    product_id, _, _ = await _stocked_product(h)
    order = await _order(h, customer_id, product_id, "20")  # 200 > 100
    assert order["status"] == "credit_hold"
    await h.post(f"/api/v3b/orders/{order['id']}/reserve", expect=409)
    assert await _balance(h, product_id) == (Decimal("50"), Decimal("0"))


async def test_ar_invoice_rejected_in_closed_period(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "Late Shipper Ltd", "10000")
    product_id, _, _ = await _stocked_product(h)
    order = await _order(h, customer_id, product_id, "5")
    await h.post(f"/api/v3b/orders/{order['id']}/reserve")
    journals_before = len(await h.sql("SELECT id FROM journal_entries"))
    await h.close_period()
    await h.post(
        f"/api/v3b/orders/{order['id']}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": "2026-02-14"},
        expect=409,
    )
    journals_after = len(await h.sql("SELECT id FROM journal_entries"))
    assert journals_after == journals_before, "no journal may be written"
    assert await _balance(h, product_id) == (Decimal("50"), Decimal("5")), "stock must not move"


async def test_ar_inventory_valuation_reconciles_to_gl(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "Valuation Check LLC", "10000")
    product_id, _, _ = await _stocked_product(h)  # 50 @ 6.00 = 300.00 on hand
    order = await _order(h, customer_id, product_id, "20")
    await h.post(f"/api/v3b/orders/{order['id']}/reserve")
    await h.post(
        f"/api/v3b/orders/{order['id']}/ship-invoice",
        params={"ship_date": IN_PERIOD.isoformat(), "due_date": "2026-02-14"},
    )
    on_hand, _ = await _balance(h, product_id)
    assert await h.account_balance("inventory") == on_hand * Decimal("6.00")


async def test_ar_inventory_adjustment_rejected_in_closed_period(harness: Harness) -> None:
    h = harness
    product_id, warehouse_id, location_id = await _stocked_product(h)
    await h.close_period()
    await h.post(
        "/api/v3b/inventory/adjust",
        json={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "location_id": location_id,
            "quantity": "5",
            "unit_cost": "6.00",
            "idempotency_key": f"closed-{uuid4().hex}",
            "accounting": _accounting(h),
        },
        expect=409,
    )
    assert await _balance(h, product_id) == (Decimal("50"), Decimal("0")), "stock must not move"
