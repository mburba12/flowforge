from decimal import Decimal
from uuid import uuid4

from flowforge.phase1b.analytics import Analytics, Metric


def test_tenant_metrics():
    a, b = uuid4(), uuid4()
    x = Analytics()
    x.record(Metric(a, "orders", Decimal("2")))
    x.record(Metric(b, "orders", Decimal("8")))
    assert x.total(a, "orders") == 2 and "8" not in x.export_csv(a)
