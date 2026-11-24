from uuid import uuid4

from flowforge.phase1b.notifications import Channel, NotificationService, Preferences


def test_preferences_and_retry():
    s = NotificationService()
    n = s.create(uuid4(), uuid4(), Channel.SMS, "x", "y", Preferences())
    assert n.status == "suppressed"
    n2 = s.create(uuid4(), uuid4(), Channel.EMAIL, "x", "y", Preferences())
    s.failed(n2, 1)
    assert n2.status == "dead"
