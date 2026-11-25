import pytest

from flowforge.phase5a.router import status


@pytest.mark.asyncio
async def test_status():
    result = await status()
    assert result["status"] == "implemented"
    assert result["tenant_authority"] == "token_only"
    assert result["production_credentials"] is False
