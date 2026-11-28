"""Every API operation is reachable from a workspace in the web app.

The server's operation catalog (/api/v1/operations) assigns each non-public operation
to a workspace; the web app renders every operation of a workspace as a typed form
(web/src/release/operations.tsx). This test fails when an operation has no workspace,
or a workspace is not served by the UI and listed in the sidebar.
"""

import re
from pathlib import Path

from flowforge.main import app
from flowforge.platform.authorization import PUBLIC, endpoint_key, iter_routes_with_paths
from flowforge.release.operations_routes import EXTENDED_WORKSPACES, operation_catalog

from .conftest import Harness

WEB = Path(__file__).resolve().parents[2] / "web" / "src"


def _sidebar_slugs() -> set[str]:
    text = (WEB / "lib" / "modules.ts").read_text(encoding="utf-8")
    return set(re.findall(r'\[\s*"([\w-]+)"\s*,\s*"[^"]+"\s*\]', text))


def _extended_ui_slugs() -> set[str]:
    text = (WEB / "release" / "slugs.ts").read_text(encoding="utf-8")
    block = text[
        text.index("EXTENDED_WORKSPACES") : text.index("export function hasExtendedWorkspace")
    ]
    return set(re.findall(r'^\s*"?([\w-]+)"?\s*:\s*\{', block, flags=re.M))


def test_every_operation_has_a_workspace() -> None:
    spec = app.openapi()
    catalog = {(o["method"], o["path"]) for o in operation_catalog(app)["operations"]}
    public = {
        (method, path)
        for route, path in iter_routes_with_paths(list(app.routes))
        if endpoint_key(route.endpoint) in PUBLIC
        for method in route.methods or ()
    }
    missing = [
        f"{method.upper()} {path}"
        for path, item in spec["paths"].items()
        for method in item
        if method in {"get", "post", "put", "patch", "delete"}
        and (method.upper(), path) not in catalog
        and (method.upper(), path) not in public
    ]
    assert not missing, missing


def test_every_workspace_is_served_and_in_the_sidebar() -> None:
    workspaces = {o["workspace"] for o in operation_catalog(app)["operations"]}
    sidebar = _sidebar_slugs()
    assert workspaces <= sidebar, sorted(workspaces - sidebar)
    assert set(EXTENDED_WORKSPACES.values()) == _extended_ui_slugs()


async def test_catalog_endpoint_describes_forms(harness: Harness) -> None:
    h = harness
    crm = await h.call("GET", "/api/v1/operations", params={"workspace": "crm"})
    assert crm["operations"] and {o["workspace"] for o in crm["operations"]} == {"crm"}
    lead = next(
        o for o in crm["operations"] if o["method"] == "POST" and o["path"] == "/api/v2/crm/leads"
    )
    assert lead["permission"] == "crm.write"
    assert lead["body"]["properties"], "request schema is inlined for the generated form"
    assert "crm_leads" in crm["tables"] or crm["tables"]
    assert (await h.client.get("/api/v1/operations")).status_code == 401
