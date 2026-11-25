from dataclasses import dataclass
from enum import StrEnum


class GateState(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


REQUIRED_GATES = (
    "staging_deployment",
    "production_deployment",
    "entra_mfa",
    "key_vault_managed_identity",
    "copilot_grounding",
    "document_intelligence",
    "provider_read_sync",
    "controlled_writeback",
    "high_risk_controls",
    "post_execution_reconciliation",
    "cross_tenant_campaign",
    "pitr_restore",
    "webhook_replay",
    "queue_replay",
    "penetration_remediation",
    "capacity_campaign",
    "privacy_signoff",
    "security_signoff",
    "pilot_acceptance",
    "billing_acceptance",
)


@dataclass(frozen=True, slots=True)
class Gate:
    name: str
    state: GateState
    evidence_uri: str


def evaluate(gates: tuple[Gate, ...]) -> tuple[bool, tuple[str, ...]]:
    indexed = {gate.name: gate for gate in gates}
    missing = tuple(
        name
        for name in REQUIRED_GATES
        if name not in indexed
        or indexed[name].state is not GateState.PASSED
        or not indexed[name].evidence_uri.startswith("https://")
    )
    return not missing, missing
