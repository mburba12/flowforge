import pytest
from pydantic import ValidationError
from flowforge.commerce_completion.schemas import LandedCostCreate
def test_landed_cost_method():
 with pytest.raises(ValidationError):LandedCostCreate(receipt_id='00000000-0000-0000-0000-000000000001',cost_type='freight',amount=1,allocation_method='invented')
