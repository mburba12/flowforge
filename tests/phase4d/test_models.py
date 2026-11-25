from decimal import Decimal

from sqlalchemy import Numeric

from flowforge.db.base import Base
from flowforge.phase4d import models  # noqa: F401

EXPECTED = {
    "canonical_entities",
    "external_entity_references",
    "entity_match_candidates",
    "entity_merge_proposals",
    "entity_merge_members",
    "entity_merge_events",
    "canonical_products",
    "product_source_links",
    "sku_crosswalks",
    "entity_relationships",
}


def test_models() -> None:
    assert EXPECTED <= set(Base.metadata.tables)
    for name in EXPECTED:
        assert "tenant_id" in Base.metadata.tables[name].columns


def test_decimal_uom() -> None:
    table = Base.metadata.tables["sku_crosswalks"]
    assert isinstance(table.c.conversion_numerator.type, Numeric)
    assert Decimal("1.5") / Decimal(3) == Decimal("0.5")


def test_no_plaintext_sensitive_columns() -> None:
    names = {
        column.name
        for table in (Base.metadata.tables[name] for name in EXPECTED)
        for column in table.columns
    }
    assert not {"ssn", "tax_identifier", "bank_account_number"} & names
