from flowforge.phase1a.mfa import RecoveryCodes


def test_recovery_single_use():
    r = RecoveryCodes.from_plain(["ABC"])
    assert r.consume("ABC")
    assert not r.consume("ABC")
