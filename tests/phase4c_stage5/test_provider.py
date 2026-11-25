import pytest

from flowforge.phase4c_stage5.providers import SandboxFinanceProvider


@pytest.mark.asyncio
async def test_provider() -> None:
    p = SandboxFinanceProvider("quickbooks_online")
    org, name = await p.connect("sandbox-code")
    assert org and name
    docs, cursor = await p.documents(org, None)
    assert len(docs) == 1 and cursor
    assert await p.verify_webhook(b"{}", "sandbox-valid-signature")
