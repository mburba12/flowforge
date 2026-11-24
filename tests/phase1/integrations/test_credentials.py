import pytest

from flowforge.phase1.integrations.credentials import CredentialsComponent


@pytest.mark.asyncio
async def test_credentials_contract() -> None:
    result = await CredentialsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "integrations.credentials"
