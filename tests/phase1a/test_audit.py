from uuid import uuid4

from flowforge.phase1a.audit import AuditChain


def test_tamper_chain():
    a = AuditChain()
    a.append(uuid4(), None, "created", "user", "1")
    a.append(uuid4(), None, "updated", "user", "1")
    assert a.verify()
