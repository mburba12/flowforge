from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from .errors import WorkflowError


class Status(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Step:
    name: str
    approvals_required: int = 1


@dataclass(slots=True)
class Instance:
    id: UUID
    steps: list[Step]
    index: int = 0
    status: Status = Status.PENDING
    approvers: set[UUID] = field(default_factory=set)


class WorkflowEngine:
    def start(self, steps: list[Step]) -> Instance:
        if not steps:
            raise WorkflowError("Workflow requires steps")
        return Instance(uuid4(), steps)

    def approve(self, i: Instance, user_id: UUID) -> None:
        if i.status != Status.PENDING:
            raise WorkflowError("Workflow is closed")
        if user_id in i.approvers:
            raise WorkflowError("Duplicate approval")
        i.approvers.add(user_id)
        if len(i.approvers) >= i.steps[i.index].approvals_required:
            i.index += 1
            i.approvers.clear()
            if i.index == len(i.steps):
                i.status = Status.APPROVED

    def reject(self, i: Instance) -> None:
        i.status = Status.REJECTED
