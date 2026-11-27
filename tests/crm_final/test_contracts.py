import pytest
from pydantic import ValidationError
from flowforge.crm_final.schemas import OpportunityTransition
def test_stage_bounded():
 with pytest.raises(ValidationError):OpportunityTransition(stage='invented',probability=50)
