from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS: list[dict[str, object]] = []
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


for path in sorted((ROOT / "src" / "flowforge").rglob("*.py")):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        continue

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            if not isinstance(decorator.func, ast.Attribute):
                continue

            method = decorator.func.attr.upper()

            if method not in HTTP_METHODS:
                continue

            route = ""

            if (
                decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                route = decorator.args[0].value

            ITEMS.append(
                {
                    "method": method,
                    "route": route,
                    "handler": node.name,
                    "file": path.relative_to(ROOT).as_posix(),
                    "line": node.lineno,
                }
            )


output_directory = ROOT / "var" / "acceptance"
output_directory.mkdir(parents=True, exist_ok=True)

output_path = output_directory / "backend-operation-inventory.json"
output_path.write_text(
    json.dumps(
        {
            "operation_count": len(ITEMS),
            "operations": ITEMS,
        },
        indent=2,
    ),
    encoding="utf-8",
)

print(f"operations={len(ITEMS)}")
