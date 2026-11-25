import pytest

from flowforge.phase4c.providers import SandboxBankingProvider


@pytest.mark.asyncio
async def test_sandbox_provider() -> None:
    p = SandboxBankingProvider()
    token, item = await p.exchange_token("sandbox-public")
    assert token and item
    assert (await p.list_accounts(token))[0].mask == "1842"
