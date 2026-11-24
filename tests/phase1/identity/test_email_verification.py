import pytest

from flowforge.phase1.identity.email_verification import EmailVerificationComponent


@pytest.mark.asyncio
async def test_email_verification_contract() -> None:
    result = await EmailVerificationComponent().execute({"tenant_id": "tenant-test"})
    assert result["accepted"] is True
    assert result["component"] == "identity.email_verification"
