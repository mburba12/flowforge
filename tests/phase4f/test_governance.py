import pytest

from flowforge.phase4f.governance import (
    AiAuthorization,
    Citation,
    GroundedAnswer,
    authorize_record,
    digest_content,
    require_grounding,
    validate_upload,
)


def test_authorization() -> None:
    c = AiAuthorization("t", "u", frozenset({"read"}), frozenset({"ap"}), frozenset({"r"}))
    assert authorize_record(c, "ap", "r")
    assert not authorize_record(c, "ar", "r")


def test_upload() -> None:
    assert validate_upload("invoice.pdf", 100) == ".pdf"
    with pytest.raises(ValueError):
        validate_upload("run.exe", 100)


def test_digest() -> None:
    assert len(digest_content(b"x")) == 64


def test_grounding() -> None:
    require_grounding(GroundedAnswer("a", (Citation("r", "ap", "now"),), "sum", ()))
    with pytest.raises(ValueError):
        require_grounding(GroundedAnswer("a", (), "sum", ()))
