from flowforge.phase1b.operations import SECURITY_HEADERS, HealthService, RateLimiter


def test_health_rate_security():
    assert HealthService().readiness(True, True).status == "ready"
    r = RateLimiter(1, 60)
    assert r.allow("x") and not r.allow("x")
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
