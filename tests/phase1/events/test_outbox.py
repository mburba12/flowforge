import pytest

from flowforge.phase1.events.outbox import OutboxComponent


@pytest.mark.asyncio
async def test_outbox_contract() -> None:
    result = await OutboxComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "events.outbox"
