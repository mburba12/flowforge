from uuid import uuid4

import pytest

from flowforge.phase1a.errors import AuthenticationError
from flowforge.phase1a.invitations import InvitationService


def test_single_use():
    s = InvitationService()
    i, t = s.issue(uuid4(), "a@example.com", "member")
    s.accept(i, t, "a@example.com")
    with pytest.raises(AuthenticationError):
        s.accept(i, t, "a@example.com")
