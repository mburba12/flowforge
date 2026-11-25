from flowforge.phase4d.normalization import (
    build_identity_fingerprint,
    normalize_domain,
    normalize_email,
    normalize_name,
    normalize_phone,
    normalize_sku,
)


def test_normalizers() -> None:
    assert normalize_name("  ACME, Inc. ") == "acme inc"
    assert normalize_email(" USER@Example.COM ") == "user@example.com"
    assert normalize_phone("+1 (810) 555-1212") == "18105551212"
    assert normalize_domain("https://www.Example.com/a") == "example.com"
    assert normalize_sku("ab-12 cd") == "AB12CD"
    assert build_identity_fingerprint("A", "B") == build_identity_fingerprint("a", "b")
