from decimal import Decimal
def duplicate_key(tenant_id:str,vendor_id:str,invoice_number:str)->str:return f"{tenant_id}:{vendor_id}:{invoice_number.strip().lower()}"
def match_variance(invoice:Decimal,receipt:Decimal)->Decimal:return invoice-receipt
def assert_match(invoice:Decimal,receipt:Decimal,tolerance:Decimal)->None:
 if abs(match_variance(invoice,receipt))>tolerance:raise ValueError("AP match tolerance exceeded")
