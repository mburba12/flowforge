import pytest

from flowforge.phase1a.errors import AuthorizationError
from flowforge.phase1a.rbac import Principal, Role, require_permission, validate_separation


def test_rbac():
    p = Principal([Role("approver", {"invoice.approve"})])
    require_permission(p, "invoice.approve")
    with pytest.raises(AuthorizationError):
        require_permission(p, "users.manage")
    validate_separation(p, {("invoice.create", "invoice.approve")})
