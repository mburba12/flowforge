import pytest

from flowforge.phase1.notifications.preferences import PreferencesComponent


@pytest.mark.asyncio
async def test_preferences_contract() -> None:
    result = await PreferencesComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "notifications.preferences"
