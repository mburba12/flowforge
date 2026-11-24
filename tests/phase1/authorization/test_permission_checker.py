import pytest

from flowforge.phase1.authorization.permission_checker import PermissionCheckerComponent


@pytest.mark.asyncio
async def test_permission_checker_contract() -> None:
    result = await PermissionCheckerComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "authorization.permission_checker"
