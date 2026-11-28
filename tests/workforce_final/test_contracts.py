from flowforge.workforce_final.schemas import CandidateCreate


def test_consent_required_by_service_contract():
    x = CandidateCreate(candidate_number="C1", name="A", email="a@b.com")
    assert not x.consent
