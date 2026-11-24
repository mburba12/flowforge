import pytest

from flowforge.phase1.identity.passwords import PasswordsComponent


@pytest.mark.asyncio
async def test_passwords_contract() -> None:
    result = await PasswordsComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "identity.passwords"
