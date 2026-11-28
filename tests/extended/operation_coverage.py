"""Which API operations has no test or audit exercised successfully?

Usage: python tests/extended/operation_coverage.py <coverage-file> [...]
Reads the records written with FLOWFORGE_OPERATION_COVERAGE and writes
var/operation-coverage.json with the operations never seen answering 2xx.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from flowforge.main import app  # noqa: E402
from flowforge.platform.authorization import PUBLIC, endpoint_key, iter_routes_with_paths  # noqa: E402

seen: set[str] = set()
for name in sys.argv[1:]:
    seen.update(
        line.strip() for line in Path(name).read_text(encoding="utf-8").splitlines() if line.strip()
    )

spec_paths = app.openapi()["paths"]
operations = []
for route, path in iter_routes_with_paths(list(app.routes)):
    if path not in spec_paths:
        continue
    for method in sorted((route.methods or set()) - {"HEAD"}):
        operations.append((method, path, endpoint_key(route.endpoint)))

missing = [
    {"operation": f"{m} {p}", "public": k in PUBLIC}
    for m, p, k in operations
    if f"{m} {k}" not in seen
]
report = {
    "operations": len(operations),
    "covered": len(operations) - len(missing),
    "not_covered": missing,
}
(ROOT / "var").mkdir(exist_ok=True)
(ROOT / "var" / "operation-coverage.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(f"operations={report['operations']} covered={report['covered']} not_covered={len(missing)}")
