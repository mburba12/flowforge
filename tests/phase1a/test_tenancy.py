from uuid import uuid4

import pytest

from flowforge.phase1a.errors import TenantIsolationError
from flowforge.phase1a.tenancy import TenantContext, require_tenant


def test_cross_tenant_denied():
    c = TenantContext(uuid4(), uuid4())
    with pytest.raises(TenantIsolationError):
        require_tenant(c, uuid4())
