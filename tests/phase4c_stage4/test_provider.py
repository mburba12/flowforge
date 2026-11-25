import pytest

from flowforge.phase4c_stage4.providers import SandboxLogisticsProvider


@pytest.mark.asyncio
async def test_provider() -> None:
    p = SandboxLogisticsProvider("ups")
    account, name = await p.connect("sandbox-code")
    assert account and name
    events, cursor = await p.tracking(account, None)
    assert len(events) == 1 and cursor
    assert await p.verify_webhook(b"{}", "sandbox-valid-signature")
