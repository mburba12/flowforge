"""Concurrent document creation in one tenant gets distinct numbers (no unique-key collisions)."""

import asyncio

from .conftest import IN_PERIOD, Harness
from .test_ar_order_to_cash import _customer, _stocked_product


async def test_concurrent_parties_get_distinct_numbers(harness: Harness) -> None:
    h = harness
    responses = await asyncio.gather(
        *(
            h.client.post("/api/v2/organizations", headers=h.owner, json={"legal_name": f"Org {i}"})
            for i in range(12)
        )
    )
    assert [r.status_code for r in responses] == [201] * 12, [r.text for r in responses]
    numbers = [r[0] for r in await h.sql("SELECT party_number FROM parties")]
    assert len(numbers) == len(set(numbers)) == 12


async def test_concurrent_orders_get_distinct_numbers(harness: Harness) -> None:
    h = harness
    customer_id = await _customer(h, "Busy Buyer", "100000")
    product_id, _, _ = await _stocked_product(h)
    body = {
        "customer_id": customer_id,
        "ledger_id": h.ledger_id,
        "period_id": h.period_id,
        "order_date": IN_PERIOD.isoformat(),
        "lines": [{"product_id": product_id, "quantity": "1", "unit_price": "10.00"}],
    }
    responses = await asyncio.gather(
        *(h.client.post("/api/v3b/orders", headers=h.owner, json=body) for _ in range(6))
    )
    assert [r.status_code for r in responses] == [201] * 6, [r.text for r in responses]
    numbers = [r[0] for r in await h.sql("SELECT order_number FROM sales_orders")]
    assert len(numbers) == len(set(numbers)) == 6
