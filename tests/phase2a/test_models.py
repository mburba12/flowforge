from flowforge.db.base import Base
from flowforge.phase2a import models  # noqa:F401


def test_tables_registered() -> None:
    expected = {
        "parties",
        "party_organizations",
        "party_people",
        "party_role_assignments",
        "party_contact_methods",
        "party_addresses",
        "party_identifiers",
        "party_relationships",
        "payment_terms",
        "party_external_references",
        "organization_units",
        "party_duplicate_candidates",
        "party_merge_history",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_scope() -> None:
    for n in [
        "parties",
        "party_organizations",
        "party_people",
        "party_role_assignments",
        "party_contact_methods",
        "party_addresses",
        "party_identifiers",
        "party_relationships",
        "payment_terms",
        "party_external_references",
        "organization_units",
        "party_duplicate_candidates",
        "party_merge_history",
    ]:
        assert "tenant_id" in Base.metadata.tables[n].columns
