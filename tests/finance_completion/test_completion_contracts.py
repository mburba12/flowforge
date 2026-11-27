from flowforge.finance_completion.schemas import ExecuteRequest
def test_idempotency_required():
 assert ExecuteRequest(idempotency_key='12345678').idempotency_key=='12345678'
