from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SearchRecord:
    tenant_id: UUID
    resource_type: str
    resource_id: str
    title: str
    content: str
    permissions: frozenset[str]


class SearchIndex:
    def __init__(self) -> None:
        self.records: list[SearchRecord] = []

    def index(self, r: SearchRecord) -> None:
        self.records = [
            x
            for x in self.records
            if not (
                x.tenant_id == r.tenant_id
                and x.resource_type == r.resource_type
                and x.resource_id == r.resource_id
            )
        ] + [r]

    def query(self, tenant_id: UUID, text: str, permissions: set[str]) -> list[SearchRecord]:
        q = text.casefold()
        return [
            r
            for r in self.records
            if r.tenant_id == tenant_id
            and (not r.permissions or bool(r.permissions & permissions))
            and q in f"{r.title} {r.content}".casefold()
        ]
