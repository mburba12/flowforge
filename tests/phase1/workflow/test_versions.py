import pytest

from flowforge.phase1.workflow.versions import VersionsComponent


@pytest.mark.asyncio
async def test_versions_contract() -> None:
    result = await VersionsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "workflow.versions"
