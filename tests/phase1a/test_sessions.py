from uuid import uuid4

import pytest

from flowforge.phase1a.errors import TokenReplayError
from flowforge.phase1a.sessions import SessionStore


def test_rotation_replay_revokes():
    s = SessionStore()
    x, t = s.create(uuid4(), uuid4())
    n = s.rotate(x.id, t)
    assert n != t
    with pytest.raises(TokenReplayError):
        s.rotate(x.id, t)
    assert x.revoked_at is not None
