import pytest

from flowforge.phase4c_stage3.providers import SandboxCommerceProvider


@pytest.mark.asyncio
async def test_provider() -> None:
    p = SandboxCommerceProvider("shopify")
    store, name = await p.connect("sandbox-code")
    assert store and name
    orders, cursor = await p.orders(store, None)
    assert len(orders) == 1 and cursor
    second, _ = await p.orders(store, cursor)
    assert second == []
