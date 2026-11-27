from decimal import Decimal
from typing import Iterable
class FinancialControlError(ValueError):pass
def assert_balanced(lines:Iterable[object])->None:
 debit=sum((Decimal(str(getattr(x,'debit',0))) for x in lines),Decimal('0'));credit=sum((Decimal(str(getattr(x,'credit',0))) for x in lines),Decimal('0'))
 if debit<=0 or debit!=credit:raise FinancialControlError(f'Journal is not balanced: debit={debit} credit={credit}')
def assert_nonnegative(amount:Decimal,name:str='amount')->None:
 if amount<0:raise FinancialControlError(f'{name} cannot be negative')
def assert_transition(current:str,target:str,allowed:dict[str,set[str]])->None:
 if target not in allowed.get(current,set()):raise FinancialControlError(f'Invalid transition {current} -> {target}')
AP_TRANSITIONS={'draft':{'submitted','cancelled'},'submitted':{'approved','rejected','held'},'held':{'submitted','cancelled'},'approved':{'posted'},'posted':{'paid','reversed'}}
AR_TRANSITIONS={'draft':{'posted','cancelled'},'posted':{'partially_paid','paid','credited','written_off'},'partially_paid':{'paid','credited','written_off'}}
