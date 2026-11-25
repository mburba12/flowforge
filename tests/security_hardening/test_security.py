from uuid import uuid4

import pytest

from flowforge.security_hardening.context import (
    TenantSecurityContext,
    require_tenant_context,
    reset_tenant_context,
    set_tenant_context,
)
from flowforge.security_hardening.redaction import redact_value
from flowforge.security_hardening.rls import rls_sql
from flowforge.security_hardening.storage import tenant_blob_path, tenant_cache_key


def test_context_required() -> None:
    with pytest.raises(RuntimeError):
        require_tenant_context()


def test_context_isolated() -> None:
    context = TenantSecurityContext(uuid4(), uuid4())
    token = set_tenant_context(context)
    try:
        assert require_tenant_context() == context
    finally:
        reset_tenant_context(token)


def test_redaction() -> None:
    value = redact_value({"access_token": "secret", "safe": "ok"})
    assert value == {"access_token": "[REDACTED]", "safe": "ok"}


def test_rls_forced() -> None:
    sql = rls_sql("bank_connections")
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "WITH CHECK" in sql


def test_tenant_namespaces() -> None:
    tenant, object_id = uuid4(), uuid4()
    assert str(tenant) in tenant_blob_path(tenant, "documents", object_id, "invoice.pdf")
    assert tenant_cache_key(tenant, "customer", "1").startswith(str(tenant))
