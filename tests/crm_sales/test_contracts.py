import pytest
from pydantic import ValidationError
from flowforge.crm_sales.schemas import QuoteLineCreate
def test_discount_bounded():
 with pytest.raises(ValidationError):QuoteLineCreate(description='x',quantity=1,unit_price=1,discount_bps=10001)
