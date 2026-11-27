import pytest
from pydantic import ValidationError

from flowforge.workforce_completion.schemas import RetirementPlanCreate


def test_retirement_bps_bounded():
    with pytest.raises(ValidationError):
        RetirementPlanCreate(code="R", name="R", employer_match_bps=10001)
