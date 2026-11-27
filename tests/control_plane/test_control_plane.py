import pytest

from flowforge.control_plane.capabilities import CAPABILITIES, registry
from flowforge.control_plane.policies import ProviderWritePolicy


def test_registry_unique_and_available():
    assert len(registry()) == len(CAPABILITIES)
    assert all(x.available() for x in CAPABILITIES if x.status.value == "implemented")


def test_all_capabilities_tenant_scoped_and_audited():
    assert all(x.tenant_scoped and x.audit_required for x in CAPABILITIES)


def test_provider_writes_safe_by_default():
    with pytest.raises(PermissionError):
        ProviderWritePolicy().assert_allowed(sandbox=True, approved=True)
