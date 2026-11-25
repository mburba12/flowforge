import pytest

from flowforge.phase4c_stage6.providers import SandboxWorkforceProvider


@pytest.mark.asyncio
async def test_provider() -> None:
    provider = SandboxWorkforceProvider("adp_workforce_now")
    organization, name = await provider.connect("sandbox-code")
    assert organization and name
    runs, cursor = await provider.payroll_runs(organization, None)
    assert len(runs) == 1 and cursor
    assert await provider.verify_webhook(b"{}", "sandbox-valid-signature")
