"""The unfiltered table browsers were retired: they exposed every column (including
password hashes) and allowed raw updates of any tenant table. The business browser
(/api/v1/business) is the only generic record browser; it is read-only and filters
sensitive columns."""

from flowforge.main import app


def test_retired_generic_browsers_are_not_served() -> None:
    paths = set(app.openapi()["paths"])
    retired = {
        p
        for p in paths
        if p.startswith(("/api/v1/catalog", "/api/v1/resources", "/api/v1/platform/"))
    }
    assert not retired, sorted(retired)
    assert "/api/v1/business/{resource}" in paths
