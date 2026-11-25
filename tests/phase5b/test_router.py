import pytest

from flowforge.phase5b.router import status


@pytest.mark.asyncio
async def test_status():
    result = await status()
    assert result["status"] == "implemented"
    assert result["production_credentials"] is False
    assert result["high_risk_execution"] is False
    assert result["table_count"] == 18
