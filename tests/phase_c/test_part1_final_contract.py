from flowforge.main import app


def test_part1_contract_is_complete() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/v1/auth/login",
        "/api/v1/me",
        "/api/v1/tenants",
        "/api/v1/business/resources",
        "/api/v1/business/{resource}",
        "/api/v2/parties/search",
        "/api/v3/vendors",
        "/api/v3/vendor-invoices",
        "/api/v3b/customers",
        "/api/v3b/products",
        "/api/v3b/orders",
        "/api/v4a/workers",
        "/api/v4a/payroll/runs",
        "/api/v4b/liabilities",
        "/api/v4b/returns",
        "/api/v4c/connections/link-session",
        "/api/v4/reconciliations/amount",
    }
    assert not (required - set(paths)), sorted(required - set(paths))
