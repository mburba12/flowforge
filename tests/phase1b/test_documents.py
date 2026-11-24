from pathlib import Path
from uuid import uuid4

import pytest

from flowforge.phase1b.documents import DocumentError, DocumentService, LocalStorage


def test_versioning_and_hold(tmp_path: Path):
    s = DocumentService(LocalStorage(tmp_path))
    t = uuid4()
    d = s.upload(t, "a.pdf", "application/pdf", b"one")
    s.upload(t, "a.pdf", "application/pdf", b"two", d)
    assert len(d.versions) == 2
    d.legal_hold = True
    with pytest.raises(DocumentError):
        s.delete(d)
