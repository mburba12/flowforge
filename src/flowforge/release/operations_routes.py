"""Operation catalog for the UI: every API operation, its workspace, permission and input schema.

The web app renders a typed form for each operation from this description, so every
operation is reachable from a workspace (see tests/workflows/test_ui_reachability.py).
"""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from flowforge.core.security import Principal, current_principal
from flowforge.db.base import Base
from flowforge.platform.authorization import (
    DECISIONS,
    EXTENDED_POLICY,
    POLICY,
    PUBLIC,
    RELEASE_MODULES,
    endpoint_key,
    extended_domain,
    iter_routes_with_paths,
)

router = APIRouter(prefix="/api/v1/operations", tags=["operations-catalog"])

# Release operations: workspace by the first segment of their permission code.
RELEASE_WORKSPACES = {
    "": "settings",
    "tenant": "settings",
    "users": "settings",
    "roles": "settings",
    "platform": "settings",
    "business": "settings",
    "audit": "audit",
    "documents": "documents",
    "workflows": "approvals",
    "notifications": "work-queue",
    "integrations": "integrations",
    "masterdata": "master-data",
    "gl": "finance",
    "ap": "ap",
    "ar": "ar",
    "inventory": "inventory",
    "workforce": "workforce",
    "payroll": "payroll",
    "tax": "tax",
    "banking": "banking",
    "shipping": "shipping",
}
# Extended operations and tables: workspace by permission domain.
EXTENDED_WORKSPACES = {
    "crm": "crm",
    "commerce": "commerce",
    "finance.advanced": "finance-advanced",
    "payroll.advanced": "payroll-tax",
    "billing": "billing",
    "manufacturing": "manufacturing",
    "intelligence": "copilot",
    "operations": "operations",
    "entities": "entities",
    "governance": "governance",
    "integrations": "integrations",
    "masterdata": "master-data",
    "workforce": "talent",
}
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def workspace_of(module: str, permission: str) -> str:
    if module in RELEASE_MODULES:
        return RELEASE_WORKSPACES.get(permission.split(".")[0], "settings")
    domain = extended_domain(module)
    return EXTENDED_WORKSPACES.get(domain or "", "settings")


def _group(path: str) -> str:
    """Resource a path acts on: the last literal segment followed by a parameter, else the last."""
    parts = [p for p in path.split("/") if p]
    for index in range(len(parts) - 1, 0, -1):
        if parts[index].startswith("{") and not parts[index - 1].startswith("{"):
            return parts[index - 1]
    literal = [p for p in parts if not p.startswith("{")]
    return literal[-1] if literal else path


def _resolve(schema: Any, components: dict[str, Any], depth: int = 0) -> Any:
    """Inline $ref schemas (depth-limited) so the client needs no schema resolver."""
    if depth > 8:
        return {}
    if isinstance(schema, dict):
        if "$ref" in schema:
            name = schema["$ref"].split("/")[-1]
            return _resolve(components.get(name, {}), components, depth + 1)
        return {k: _resolve(v, components, depth + 1) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_resolve(v, components, depth + 1) for v in schema]
    return schema


@lru_cache(maxsize=1)
def _catalog(app: Any) -> dict[str, Any]:
    spec = app.openapi()
    components = spec.get("components", {}).get("schemas", {})
    operations: list[dict[str, Any]] = []
    for route, path in iter_routes_with_paths(list(app.routes)):
        if not route.include_in_schema:
            continue
        key = endpoint_key(route.endpoint)
        if key in PUBLIC:
            continue
        permission = POLICY.get(key, EXTENDED_POLICY.get(key))
        if permission is None:
            continue  # denied by default; never offered in the UI
        item = spec["paths"].get(path, {})
        for method in METHODS:
            if method not in (route.methods or set()):
                continue
            op = item.get(method.lower())
            if op is None:
                continue
            body = op.get("requestBody", {}).get("content", {}).get("application/json", {})
            operations.append(
                {
                    "id": op.get("operationId", f"{method} {path}"),
                    "method": method,
                    "path": path,
                    "summary": op.get("summary", ""),
                    "group": _group(path),
                    "workspace": workspace_of(route.endpoint.__module__, permission),
                    "permission": permission,
                    "decision_permission": DECISIONS.get(key, ("", ""))[1],
                    "parameters": [
                        {
                            "name": p["name"],
                            "in": p["in"],
                            "required": bool(p.get("required")),
                            "schema": _resolve(p.get("schema", {}), components),
                        }
                        for p in op.get("parameters", [])
                        if p.get("in") in {"path", "query"}
                    ],
                    "body": _resolve(body["schema"], components) if body else None,
                }
            )
    tables: dict[str, set[str]] = {}
    for mapper in Base.registry.mappers:
        table = getattr(mapper, "local_table", None)
        if table is None or "tenant_id" not in table.c:
            continue
        module = mapper.class_.__module__
        # Models live beside the routes module of their package (pkg.models ~ pkg.routes).
        domain = extended_domain(module) or extended_domain(module.rsplit(".", 1)[0] + ".routes")
        if domain is None:
            continue
        tables.setdefault(EXTENDED_WORKSPACES[domain], set()).add(table.name)
    return {
        "operations": sorted(operations, key=lambda o: (o["workspace"], o["group"], o["path"])),
        "tables": {k: sorted(v) for k, v in tables.items()},
    }


def operation_catalog(app: Any) -> dict[str, Any]:
    return _catalog(app)


@router.get("")
async def list_operations(
    request: Request,
    _: Annotated[Principal, Depends(current_principal)],
    workspace: Annotated[str | None, Query(max_length=60)] = None,
) -> dict[str, Any]:
    catalog = operation_catalog(request.app)
    operations = catalog["operations"]
    if workspace:
        operations = [o for o in operations if o["workspace"] == workspace]
    tables = catalog["tables"]
    return {
        "workspace": workspace,
        "operations": operations,
        "tables": tables.get(workspace, []) if workspace else tables,
    }
