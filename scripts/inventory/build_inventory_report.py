"""Assemble the read-only integration inventory report.

Usage (host, stdlib only):
    python -I build_inventory_report.py <out_dir> <project_root> <api_base_url>

Reads <out_dir>/openapi.json, routes.json, db.json. If FF_INVENTORY_TOKEN is set
in the environment, performs authenticated GET requests only (never POST/PUT/
PATCH/DELETE). Writes inventory-report.txt plus CSV detail files.
"""

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(sys.argv[1])
ROOT = Path(sys.argv[2])
API = sys.argv[3].rstrip("/")
TOKEN = os.environ.get("FF_INVENTORY_TOKEN", "")
FALLBACK_PREFIXES = ["/api/v1/", "/api/v3/", "/api/v3b/", "/api/v4a/", "/api/v4b/", "/api/v4c/"]
RELEASE_MODULES = {"ap", "ar", "orders", "payroll", "tax", "finance"}

openapi = json.loads((OUT / "openapi.json").read_text(encoding="utf-8"))
routes = json.loads((OUT / "routes.json").read_text(encoding="utf-8"))
db = json.loads((OUT / "db.json").read_text(encoding="utf-8"))

lines: list[str] = []


def kv(key, value):
    lines.append(f"{key}={value}")


def section(title):
    lines.append("")
    lines.append("=" * 80)
    lines.append(title)
    lines.append("=" * 80)


def write_csv(name, rows, fields):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()})


# ---------------------------------------------------------------- OpenAPI
ops = []
for path, item in openapi.get("paths", {}).items():
    for method, op in item.items():
        if method.lower() not in {"get", "post", "put", "patch", "delete"}:
            continue
        ops.append({
            "method": method.upper(), "path": path,
            "operation_id": op.get("operationId", ""),
            "tags": op.get("tags", []),
            "secured": bool(op.get("security")) or any(
                p.get("in") == "header" and p.get("name", "").lower() == "authorization"
                for p in op.get("parameters", [])),
        })
op_keys = {(o["method"], o["path"]) for o in ops}


def path_prefix(p):
    m = re.match(r"^(/api/v[0-9a-z]+|/[^/]+)", p)
    return m.group(1) if m else p


# ---------------------------------------------------------------- frontend
web = ROOT / "web" / "src"
bm_src = (web / "lib" / "business-modules.ts").read_text(encoding="utf-8")
rp_src = (web / "lib" / "resource-paths.ts").read_text(encoding="utf-8")
fe_aliases = dict(re.findall(r'"([^"]+)":"([^"]+)"', rp_src.split("businessReadPath")[0]))
modules = []
for m in re.finditer(r'(?:"([^"]+)"|([\w-]+)):\{title:"([^"]+)".*?resources:\[([^\]]*)\].*?actions:\[([^\]]*)\]', bm_src):
    slug = m.group(1) or m.group(2)
    modules.append({
        "slug": slug, "title": m.group(3),
        "resources": re.findall(r'"([^"]+)"', m.group(4)),
        "actions": re.findall(r'"([^"]+)"', m.group(5)),
    })

pages = []
for page in sorted((web / "app").rglob("page.tsx")):
    src = page.read_text(encoding="utf-8", errors="replace")
    comps = sorted(set(re.findall(r"import\s*\{([^}]+)\}\s*from\s*\"@/components/", src)))
    pages.append({"page": str(page.relative_to(web / "app")).replace("\\", "/"),
                  "components": ";".join(c.strip() for c in comps)})

# ---------------------------------------------------------------- database
tables = db.get("tables") or []
public_tenant_tables = {t["table"]: t for t in tables if t["schema"] == "public" and "tenant_id" in (t.get("tenant_columns") or [])}
backend_aliases = routes.get("business_aliases") or {}


def resolve_table(alias):
    for cand in backend_aliases.get(alias, [alias.replace("-", "_")]):
        if cand in public_tenant_tables:
            return public_tenant_tables[cand]
    return None


# ---------------------------------------------------------------- probe
def get(path):
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"})
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        body, status = e.read(), e.code
    except Exception as e:  # noqa: BLE001
        return {"status": "NO_RESPONSE", "ms": int((time.time() - start) * 1000), "detail": repr(e)[:160], "count": ""}
    ms = int((time.time() - start) * 1000)
    count, detail = "", ""
    try:
        data = json.loads(body or b"null")
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            if isinstance(data.get("total"), int):
                count = data["total"]
            elif isinstance(data.get("items"), list):
                count = len(data["items"])
            if status >= 400:
                detail = json.dumps(data.get("detail", data))[:160]
    except Exception:  # noqa: BLE001
        detail = body[:160].decode("utf-8", "replace") if status >= 400 else ""
    return {"status": status, "ms": ms, "count": count, "detail": detail}


probe_rows = []
if TOKEN:
    seen = set()
    targets = [("me", "/api/v1/me")]
    for m in modules:
        for r in m["resources"]:
            p = "/api/v1/business/" + fe_aliases.get(r, r.replace("/", "-"))
            targets.append((f"frontend:{m['slug']}:{r}", p))
    for o in ops:
        if o["method"] == "GET" and "{" not in o["path"] and not o["path"].endswith(("openapi.json", "/docs", "/redoc")):
            targets.append(("openapi", o["path"]))
    for source, p in targets:
        if p in seen:
            continue
        seen.add(p)
        res = get(p)
        probe_rows.append({"source": source, "path": p, **res})

probe_by_path = {r["path"]: r for r in probe_rows}

# ---------------------------------------------------------------- report
section("FLOWFORGE INTEGRATION INVENTORY (READ-ONLY)")
kv("GENERATED_AT", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
kv("API_BASE_URL", API)
kv("AUTHENTICATED_PROBE", "PERFORMED" if TOKEN else "SKIPPED (status codes UNKNOWN)")
kv("MUTATING_REQUESTS_SENT", 0)

section("1. LIVE API (OpenAPI)")
kv("OPENAPI_PATHS", len(openapi.get("paths", {})))
kv("OPENAPI_OPERATIONS", len(ops))
for meth, n in sorted(Counter(o["method"] for o in ops).items()):
    kv(f"OPERATIONS_{meth}", n)
for pre, n in sorted(Counter(path_prefix(o["path"]) for o in ops).items(), key=lambda x: -x[1]):
    kv(f"PREFIX[{pre}]", n)
odd = sorted({o["path"] for o in ops if re.search(r"^/api/v\w+/(?:.*/)?api/v\w+", o["path"])})
kv("DOUBLE_PREFIX_PATHS", len(odd))
for p in odd:
    lines.append(f"  {p}")
generic = sorted({o["path"] for o in ops if re.search(r"/\{resource\}", o["path"])})
kv("GENERIC_RESOURCE_PATHS", len(generic))
for p in generic:
    lines.append(f"  {p}")

section("2. LIVE ROUTE SECURITY SHAPE (from mounted FastAPI routes)")
live = routes.get("live_routes", [])
kv("LIVE_API_ROUTES", len(live))
live_keys = {(m, r["path"]) for r in live for m in r["methods"]}
kv("LIVE_ROUTES_NOT_IN_OPENAPI", len(live_keys - op_keys))
kv("OPENAPI_OPS_NOT_IN_LIVE_WALK", len(op_keys - live_keys))
dup = Counter((m, r["path"]) for r in live for m in r["methods"])
dups = sorted(k for k, n in dup.items() if n > 1)
kv("DUPLICATE_METHOD_PATH", len(dups))
for m, p in dups:
    lines.append(f"  {m} {p}")
public_like = re.compile(r"(health|/auth/login|/auth/bootstrap|openapi|docs|redoc)")
no_principal = [r for r in live if not r["requires_principal"] and not public_like.search(r["path"])]
kv("ROUTES_WITHOUT_PRINCIPAL_DEPENDENCY", len(no_principal))
for r in sorted(no_principal, key=lambda r: r["path"])[:80]:
    lines.append(f"  {','.join(r['methods'])} {r['path']}  [{r['module']}]")
if len(no_principal) > 80:
    lines.append(f"  ... {len(no_principal) - 80} more in routes.csv")
mutating = [r for r in live if set(r["methods"]) & {"POST", "PUT", "PATCH", "DELETE"}]
mut_no_perm = [r for r in mutating if r["requires_principal"] and not r.get("calls_require_permission") and not r.get("mentions_permission")
               and not public_like.search(r["path"])]
kv("MUTATING_ROUTES", len(mutating))
kv("MUTATING_ROUTES_WITH_NO_PERMISSION_MARKER_IN_HANDLER", len(mut_no_perm))
lines.append("  NOTE=marker scan is heuristic (handler source text only); services may check permissions deeper.")
kv("ROUTES_BY_MODULE_PACKAGE", "")
for pkg, n in sorted(Counter(".".join((r["module"] or "?").split(".")[:2]) for r in live).items(), key=lambda x: -x[1]):
    lines.append(f"  {pkg}={n}")

section("3. SOURCE ROUTERS vs LIVE MOUNTING")
src = routes.get("source_routers", [])
for st, n in sorted(Counter(r["status"] for r in src).items()):
    kv(f"SOURCE_ROUTERS_{st}", n)
for r in sorted(src, key=lambda r: (r["status"], r["module"])):
    if r["status"] in ("UNMOUNTED", "PARTIAL"):
        lines.append(f"  {r['status']} {r['module']}.{r['attribute']} prefix={r['prefix'] or '-'} routes={r['mounted_route_count']}/{r['route_count']}")
import_errors = [e for e in routes.get("errors", []) if e.get("stage") == "import_module"]
kv("MODULE_IMPORT_ERRORS", len(import_errors))
for e in import_errors[:40]:
    lines.append(f"  {e['module']}: {e['error'][:200]}")

section("4. DATABASE")
for k in ("database", "server_version", "current_user", "is_superuser", "bypass_rls", "alembic_versions", "policy_count",
          "legacy_organizations", "legacy_users", "permission_catalog_public", "permission_catalog_identity"):
    kv(k.upper(), json.dumps(db.get(k)))
kv("TABLES_TOTAL", len(tables))
kv("TABLES_RLS_ENABLED", sum(1 for t in tables if t["rls"]))
kv("TABLES_FORCE_RLS", sum(1 for t in tables if t["force_rls"]))
by_schema = defaultdict(lambda: [0, 0, 0])
for t in tables:
    s = by_schema[t["schema"]]
    s[0] += 1
    s[1] += 1 if t["rows"] else 0
    s[2] += t["rows"] or 0
for s, (n, ne, rows) in sorted(by_schema.items()):
    lines.append(f"  SCHEMA[{s}] tables={n} nonempty={ne} rows={rows}")
lines.append("NONEMPTY_TABLES (schema.table=rows):")
for t in sorted((t for t in tables if t["rows"]), key=lambda t: (t["schema"], t["table"])):
    lines.append(f"  {t['schema']}.{t['table']}={t['rows']}")
pub = [t for t in tables if t["schema"] == "public" and t["table"] != "alembic_version"]
no_tenant = [t for t in pub if not t.get("tenant_columns")]
kv("PUBLIC_TABLES_WITHOUT_TENANT_COLUMN", len(no_tenant))
lines.append("  " + ", ".join(t["table"] for t in no_tenant))
kv("TABLES_WITHOUT_PRIMARY_KEY", sum(1 for t in tables if not t["has_pk"]))
floats = [(t, c) for t in tables for c in (t.get("float_money_columns") or [])]
kv("FLOAT_TYPED_MONEY_LIKE_COLUMNS", len(floats))
for t, c in floats:
    lines.append(f"  {t['schema']}.{t['table']}.{c}")

section("5. IDENTITY, TENANTS, PERMISSIONS")
for tn in db.get("tenants") or []:
    lines.append(f"  TENANT slug={tn['slug']} status={tn['status']} deleted={tn['is_deleted']} id={tn['id']}")
for p in db.get("tenant_principals") or []:
    lines.append(f"  PRINCIPAL tenant={p['tenant_slug']} user={p['email_masked']} active={p['active']} roles={p['roles']} permissions={p['permission_count']}")

section("6. FRONTEND RESOURCE MATRIX")
kv("FRONTEND_PAGES", len(pages))
for p in pages:
    lines.append(f"  PAGE {p['page']} -> {p['components'] or '-'}")
fe_rows = []
for m in modules:
    for r in m["resources"]:
        alias = fe_aliases.get(r, r.replace("/", "-"))
        read_path = f"/api/v1/business/{alias}"
        table = resolve_table(alias)
        dedicated = [pre + r for pre in FALLBACK_PREFIXES if ("GET", pre + r) in op_keys]
        pr = probe_by_path.get(read_path, {})
        stem = alias.split("/")[-1].replace("-", "_").rstrip("s")
        similar = sorted(t for t in public_tenant_tables if stem and stem in t)[:4] if table is None else []
        if table is None:
            blocker = "ALIAS_TABLE_MISSING_404"
        else:
            blocker = "GENERIC_ROUTER_500_MISSING_GREENLET" if (not TOKEN or pr.get("status") == 500) else "NONE"
        fe_rows.append({
            "module": m["slug"], "release_critical": m["slug"] in RELEASE_MODULES, "resource": r,
            "read_path": read_path, "backend_table": f"public.{table['table']}" if table else "",
            "table_rows_all_tenants": table["rows"] if table else "",
            "dedicated_get_route": ";".join(dedicated),
            "probe_status": pr.get("status", "UNKNOWN"), "probe_count": pr.get("count", ""),
            "probe_detail": pr.get("detail", ""), "blocker": blocker,
            "similar_tables": ";".join(similar),
            "actions": ";".join(m["actions"]),
        })
kv("FRONTEND_MODULES", len(modules))
kv("FRONTEND_RESOURCES", len(fe_rows))
kv("RESOURCES_WITH_BACKEND_TABLE", sum(1 for r in fe_rows if r["backend_table"]))
kv("RESOURCES_WITHOUT_BACKEND_TABLE", sum(1 for r in fe_rows if not r["backend_table"]))
kv("RESOURCES_WITH_DEDICATED_GET_ROUTE", sum(1 for r in fe_rows if r["dedicated_get_route"]))
if TOKEN:
    for st, n in sorted(Counter(str(r["probe_status"]) for r in fe_rows).items()):
        kv(f"FRONTEND_PROBE_STATUS_{st}", n)
for r in fe_rows:
    flag = "*" if r["release_critical"] else " "
    lines.append(f" {flag}{r['module']:<15} {r['resource']:<28} table={r['backend_table'] or '-':<36} rows={str(r['table_rows_all_tenants']):<6} "
                 f"probe={r['probe_status']} dedicated={r['dedicated_get_route'] or '-'} blocker={r['blocker']}"
                 + (f" similar={r['similar_tables']}" if r["similar_tables"] else ""))
lines.append("  (* = release-critical module)")

section("7. AUTHENTICATED GET PROBE")
if not TOKEN:
    lines.append("SKIPPED: set credentials and rerun to fill status codes (see script help).")
else:
    for st, n in sorted(Counter(str(r["status"]) for r in probe_rows).items()):
        kv(f"PROBE_STATUS_{st}", n)
    for r in probe_rows:
        if r["status"] != 200:
            lines.append(f"  {r['status']} {r['path']} {r['detail']}")

section("8. COLLECTION ERRORS")
for e in routes.get("errors", []):
    if e.get("stage") != "import_module":
        lines.append(f"  {e}")
kv("END", "OK")

(OUT / "inventory-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
write_csv("routes.csv", live, ["methods", "path", "operation_id", "module", "function", "requires_principal", "uses_tenant_db",
                               "calls_require_permission", "mentions_permission", "mentions_tenant_id", "mentions_audit", "tags"])
write_csv("source_routers.csv", src, ["status", "module", "attribute", "prefix", "route_count", "mounted_route_count", "tags"])
write_csv("tables.csv", tables, ["schema", "table", "rows", "tenant_columns", "has_pk", "fk_out", "rls", "force_rls", "float_money_columns"])
write_csv("frontend_resources.csv", fe_rows, list(fe_rows[0].keys()) if fe_rows else ["module"])
if probe_rows:
    write_csv("probe.csv", probe_rows, ["source", "path", "status", "ms", "count", "detail"])
print(str(OUT / "inventory-report.txt"))
