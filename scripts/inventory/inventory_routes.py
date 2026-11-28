"""Read-only route inventory. Runs INSIDE the API container via stdin:

    docker exec -i <api-container> python - < inventory_routes.py

Prints one JSON document on stdout. Imports application modules but never
starts the server, opens a database session, or writes files.
"""

import importlib
import inspect
import io
import json
import logging
import pkgutil
import sys
import warnings

REAL_STDOUT = sys.stdout
NOISE = io.StringIO()
sys.stdout = NOISE
sys.stderr = NOISE
logging.disable(logging.CRITICAL)
warnings.simplefilter("ignore")

result = {"errors": [], "live_routes": [], "source_routers": [], "business_aliases": None}

try:
    from fastapi import APIRouter
    from fastapi.routing import APIRoute

    import flowforge
    from flowforge.main import app
except Exception as exc:  # noqa: BLE001
    result["errors"].append({"stage": "import_app", "error": repr(exc)})
    REAL_STDOUT.write(json.dumps(result))
    sys.exit(0)


def dependency_names(dependant):
    names = []
    for sub in dependant.dependencies:
        call = getattr(sub, "call", None)
        if call is not None:
            names.append(getattr(call, "__qualname__", repr(call)))
        names.extend(dependency_names(sub))
    return names


def source_markers(func):
    try:
        src = inspect.getsource(func)
    except Exception:  # noqa: BLE001
        return {"source_available": False}
    return {
        "source_available": True,
        "calls_require_permission": "require_permission" in src or "has_permission" in src,
        "mentions_permission": "permission" in src.lower(),
        "mentions_tenant_id": "tenant_id" in src,
        "mentions_audit": "audit" in src.lower(),
    }


def context_dependency_names(ctx):
    names = []
    for dep in getattr(ctx, "dependencies", None) or []:
        call = getattr(dep, "dependency", None)
        if call is not None:
            names.append(getattr(call, "__qualname__", repr(call)))
    return names


def flatten(route_list, prefix="", inherited=()):
    """Yield (full_path, APIRoute, inherited_dependency_names).

    FastAPI >= 0.16x stores include_router() results as lazy _IncludedRouter
    wrappers, so app.routes no longer contains the APIRoute objects directly.
    """
    for r in route_list:
        if isinstance(r, APIRoute):
            yield prefix + r.path, r, list(inherited)
        elif type(r).__name__ == "_IncludedRouter":
            ctx = r.include_context
            yield from flatten(
                r.original_router.routes,
                prefix + (getattr(ctx, "prefix", "") or ""),
                tuple(inherited) + tuple(context_dependency_names(ctx)),
            )


live_endpoint_ids = set()
for full_path, route, inherited_deps in flatten(app.routes):
    ep = route.endpoint
    live_endpoint_ids.add(id(ep))
    deps = sorted(set(dependency_names(route.dependant)) | set(inherited_deps))
    entry = {
        "path": full_path,
        "methods": sorted(m for m in route.methods if m != "HEAD"),
        "name": route.name,
        "operation_id": route.operation_id or route.unique_id,
        "tags": [str(t) for t in (route.tags or [])],
        "module": getattr(ep, "__module__", None),
        "function": getattr(ep, "__qualname__", None),
        "dependencies": deps,
        "requires_principal": any("current_principal" in d or "principal" in d.lower() for d in deps),
        "uses_tenant_db": any("get_tenant_db" in d for d in deps),
        "uses_bootstrap_db": any(d.endswith("get_db") for d in deps),
        "include_in_schema": route.include_in_schema,
    }
    entry.update(source_markers(ep))
    result["live_routes"].append(entry)

seen_routers = {}
for mod_info in pkgutil.walk_packages(flowforge.__path__, "flowforge."):
    name = mod_info.name
    if ".tests" in name or name.endswith(".__main__"):
        continue
    try:
        module = importlib.import_module(name)
    except BaseException as exc:  # noqa: BLE001
        result["errors"].append({"stage": "import_module", "module": name, "error": repr(exc)[:300]})
        continue
    for attr, obj in list(vars(module).items()):
        if not isinstance(obj, APIRouter):
            continue
        key = id(obj)
        api_routes = [r for r in obj.routes if isinstance(r, APIRoute)]
        endpoint_modules = {getattr(r.endpoint, "__module__", None) for r in api_routes}
        defined_here = name in endpoint_modules or not api_routes
        if key in seen_routers:
            if defined_here and seen_routers[key]["module"] not in endpoint_modules:
                seen_routers[key]["module"] = name
                seen_routers[key]["attribute"] = attr
            continue
        mounted = sum(1 for r in api_routes if id(r.endpoint) in live_endpoint_ids)
        seen_routers[key] = {
            "module": name,
            "attribute": attr,
            "prefix": obj.prefix,
            "tags": [str(t) for t in (obj.tags or [])],
            "route_count": len(api_routes),
            "mounted_route_count": mounted,
            "paths": sorted({f"{','.join(sorted(m for m in r.methods if m != 'HEAD'))} {r.path}" for r in api_routes}),
        }

for info in seen_routers.values():
    if info["route_count"] == 0:
        info["status"] = "EMPTY"
    elif info["mounted_route_count"] == 0:
        info["status"] = "UNMOUNTED"
    elif info["mounted_route_count"] < info["route_count"]:
        info["status"] = "PARTIAL"
    else:
        info["status"] = "MOUNTED"
    result["source_routers"].append(info)

try:
    from flowforge.resource_contracts import router as business_router

    result["business_aliases"] = {k: list(v) for k, v in business_router.ALIASES.items()}
except Exception as exc:  # noqa: BLE001
    result["errors"].append({"stage": "business_aliases", "error": repr(exc)})

result["import_noise_chars"] = len(NOISE.getvalue())
REAL_STDOUT.write(json.dumps(result))
REAL_STDOUT.flush()
