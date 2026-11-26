import pytest
from pydantic import ValidationError
from flowforge.master_data.schemas import RelationshipCreate,PaymentTermCreate
def test_relationship_dates_ordered():
 from datetime import date
 with pytest.raises(ValidationError):RelationshipCreate(target_party_id='00000000-0000-0000-0000-000000000001',relationship_type='parent',effective_from=date(2026,2,1),effective_to=date(2026,1,1))
def test_payment_discount_bps_bounded():
 with pytest.raises(ValidationError):PaymentTermCreate(code='X',name='X',due_days=30,discount_basis_points=10001)
