from uuid import uuid4

from flowforge.phase1a.outbox import Outbox


def test_dead_letter():
    o = Outbox(2)
    e = o.add(uuid4(), "user.created", {})
    o.failure(e)
    assert not e.dead
    o.failure(e)
    assert e.dead
