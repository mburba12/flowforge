import pytest
from pydantic import ValidationError
from flowforge.finance_final.schemas import AllocationExecute
def test_allocation_requires_targets():
 with pytest.raises(ValidationError):AllocationExecute(idempotency_key='12345678',journal_date='2026-01-01',period_id='00000000-0000-0000-0000-000000000001',source_account_id='00000000-0000-0000-0000-000000000002',amount='10',targets=[])
