from uuid import uuid4

from flowforge.phase1b.search import SearchIndex, SearchRecord


def test_tenant_permission_filter():
    a, b = uuid4(), uuid4()
    i = SearchIndex()
    i.index(SearchRecord(a, "doc", "1", "Invoice", "secret", frozenset({"docs.read"})))
    assert not i.query(b, "invoice", {"docs.read"})
    assert not i.query(a, "invoice", set())
    assert i.query(a, "invoice", {"docs.read"})
