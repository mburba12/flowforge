from decimal import Decimal
from flowforge.finance_workflows.service import FinanceWorkflowService
def test_reconciliation_ready_without_database():
 service=object.__new__(FinanceWorkflowService)
 result=service.reconcile(Decimal('10'),Decimal('10'),Decimal('0'),'a','b')
 assert result['ready'] and result['metrics']['variance']==0
def test_reconciliation_blocked_outside_tolerance():
 service=object.__new__(FinanceWorkflowService)
 result=service.reconcile(Decimal('10'),Decimal('9'),Decimal('.5'),'a','b')
 assert not result['ready'] and result['blockers']
