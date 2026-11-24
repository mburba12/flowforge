from flowforge.phase2a.normalization import (
    normalize_email,
    normalize_identifier,
    normalize_name,
    normalize_phone,
)


def test_normalization() -> None:
    assert normalize_name("Acme, Inc.") == "acme inc"
    assert normalize_email(" A@EXAMPLE.COM ") == "a@example.com"
    assert normalize_phone("(810) 555-1212") == "8105551212"
    assert normalize_identifier("12-345 6789") == "123456789"
