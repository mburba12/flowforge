import pytest

from flowforge.phase5a.policy import ProductAccess, authorize, safe_telemetry_dimensions


def test_access():
    authorize(ProductAccess(frozenset({"ap.view"}), frozenset({"ap"})), "ap.view", "ap")


def test_permission():
    with pytest.raises(PermissionError):
        authorize(ProductAccess(frozenset(), frozenset({"ap"})), "ap.view", "ap")


def test_entitlement():
    with pytest.raises(PermissionError):
        authorize(ProductAccess(frozenset({"ap.view"}), frozenset()), "ap.view", "ap")


def test_telemetry():
    with pytest.raises(ValueError):
        safe_telemetry_dimensions({"access_token": "secret"})
