import pytest

from flowforge.phase1.notifications.templates import TemplatesComponent


@pytest.mark.asyncio
async def test_templates_contract() -> None:
    result = await TemplatesComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "notifications.templates"
