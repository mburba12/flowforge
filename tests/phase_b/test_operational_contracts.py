import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def test_phase_b_operator_scripts_exist() -> None:
    required = [
        "scripts/local/Start-FlowForge.ps1",
        "scripts/local/Stop-FlowForge.ps1",
        "scripts/local/Restart-FlowForge.ps1",
        "scripts/local/Get-FlowForgeStatus.ps1",
        "scripts/local/Backup-FlowForge.ps1",
        "scripts/local/Restore-FlowForge.ps1",
        "scripts/acceptance/Invoke-PhaseBBackend.ps1",
        "scripts/acceptance/Invoke-MigrationRehearsal.ps1",
        "scripts/acceptance/Invoke-FailureRecovery.ps1",
    ]

    assert all((ROOT / relative_path).is_file() for relative_path in required)


def test_runtime_session_installs_tenant_context() -> None:
    text = (ROOT / "src/flowforge/db/session.py").read_text(encoding="utf-8")

    assert "app.current_tenant_id" in text
    assert "SET LOCAL" in text or "set_config" in text


def test_compose_does_not_hardcode_runtime_url() -> None:
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "env_file" in text
    assert "FLOWFORGE_DATABASE_URL:" not in text


def test_no_empty_route_handlers() -> None:
    violations: list[str] = []

    for path in (ROOT / "src/flowforge").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.FunctionDef | ast.AsyncFunctionDef,
            ):
                continue

            is_route = any(
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr in HTTP_METHODS
                for decorator in node.decorator_list
            )

            if is_route and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                violations.append(f"{path}:{node.lineno}")

    assert not violations


def test_local_runtime_preserves_volumes_by_default() -> None:
    text = (ROOT / "scripts/local/Stop-FlowForge.ps1").read_text(encoding="utf-8")

    assert "down -v" not in text
    assert "docker compose stop" in text
