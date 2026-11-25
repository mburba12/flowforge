import pytest

from flowforge.phase4c_stage2.providers import SandboxStripeProvider


@pytest.mark.asyncio
async def test_provider() -> None:
    p = SandboxStripeProvider()
    a, m = await p.connect("sandbox-code")
    assert a and m
    assert len(await p.list_payments(a)) == 1
    assert await p.verify_webhook(b"{}", "sandbox-valid-signature")
