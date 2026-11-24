import pytest

from flowforge.phase1.authorization.policies import PoliciesComponent


@pytest.mark.asyncio
async def test_policies_contract() -> None:
    result = await PoliciesComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "authorization.policies"
