import pytest

from flowforge.phase4c_stage7.providers import SandboxEngagementProvider


@pytest.mark.asyncio
async def test_provider() -> None:
    provider = SandboxEngagementProvider("salesforce_sales_cloud")
    organization, name = await provider.connect("sandbox-code")
    assert organization and name
    opportunities, cursor = await provider.opportunities(organization, None)
    assert len(opportunities) == 1 and cursor
    assert await provider.verify_webhook(b"{}", "sandbox-valid-signature")
