import pytest
from pydantic import ValidationError
from flowforge.commerce_final.schemas import TransferCreate
def test_transfer_warehouses_differ():
 with pytest.raises(ValidationError):TransferCreate(number='T',product_id='00000000-0000-0000-0000-000000000001',source_warehouse_id='00000000-0000-0000-0000-000000000002',target_warehouse_id='00000000-0000-0000-0000-000000000002',quantity=1)
