from uuid import uuid4

import pytest

from flowforge.phase1a.errors import WorkflowError
from flowforge.phase1a.workflow import Status, Step, WorkflowEngine


def test_parallel_approval():
    e = WorkflowEngine()
    i = e.start([Step("review", 2)])
    u = uuid4()
    e.approve(i, u)
    with pytest.raises(WorkflowError):
        e.approve(i, u)
    e.approve(i, uuid4())
    assert i.status == Status.APPROVED
