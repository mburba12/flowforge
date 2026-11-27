import pytest
from pydantic import ValidationError
from flowforge.bg08_final.schemas import PlanCreate
def test_interval_bounded():
 with pytest.raises(ValidationError):PlanCreate(code='x',name='x',billing_interval='x',price=1,currency_code='USD')
