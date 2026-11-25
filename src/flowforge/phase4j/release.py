from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReleaseGate:
    name: str
    passed: bool
    evidence: str


REQUIRED_GATES = (
    "single_alembic_head",
    "clean_working_tree",
    "no_tracked_secrets",
    "ruff",
    "format",
    "mypy",
    "tests",
    "rls_inventory",
    "restore_drill",
    "copilot_evaluation",
    "approval_rollback",
    "provider_contracts",
)


def evaluate_release(gates: tuple[ReleaseGate, ...]) -> tuple[bool, tuple[str, ...]]:
    values = {gate.name: gate for gate in gates}
    missing = tuple(
        name
        for name in REQUIRED_GATES
        if name not in values or not values[name].passed or not values[name].evidence
    )
    return not missing, missing
