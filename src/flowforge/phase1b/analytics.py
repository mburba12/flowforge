from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Metric:
    tenant_id: UUID
    code: str
    value: Decimal


class Analytics:
    def __init__(self) -> None:
        self.metrics: list[Metric] = []

    def record(self, m: Metric) -> None:
        self.metrics.append(m)

    def total(self, tenant_id: UUID, code: str) -> Decimal:
        return sum(
            (m.value for m in self.metrics if m.tenant_id == tenant_id and m.code == code),
            Decimal("0"),
        )

    def export_csv(self, tenant_id: UUID) -> str:
        rows = ["code,value"]
        rows.extend(f"{m.code},{m.value}" for m in self.metrics if m.tenant_id == tenant_id)
        return "\n".join(rows)
