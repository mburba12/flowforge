from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinanceProviderDefinition:
    code: str
    family: str
    auth_model: str
    capabilities: tuple[str, ...]


PROVIDERS = {
    x.code: x
    for x in (
        FinanceProviderDefinition(
            "quickbooks_online",
            "accounting",
            "oauth2",
            ("coa", "customers", "vendors", "invoices", "bills", "journals", "payments"),
        ),
        FinanceProviderDefinition(
            "quickbooks_desktop",
            "accounting_desktop",
            "web_connector",
            ("coa", "customers", "vendors", "invoices", "bills", "journals"),
        ),
        FinanceProviderDefinition(
            "xero",
            "accounting",
            "oauth2",
            ("coa", "contacts", "invoices", "bills", "journals", "payments"),
        ),
        FinanceProviderDefinition(
            "sage_intacct",
            "erp",
            "web_services",
            ("entities", "coa", "ap", "ar", "journals", "dimensions"),
        ),
        FinanceProviderDefinition(
            "sage_50",
            "accounting_desktop",
            "connector",
            ("coa", "customers", "vendors", "invoices", "bills"),
        ),
        FinanceProviderDefinition(
            "netsuite",
            "erp",
            "oauth2_or_tba",
            ("subsidiaries", "coa", "ap", "ar", "journals", "purchase_orders"),
        ),
        FinanceProviderDefinition(
            "dynamics_365_business_central",
            "erp",
            "oauth2",
            ("companies", "coa", "ap", "ar", "journals", "purchase_orders"),
        ),
        FinanceProviderDefinition(
            "dynamics_365_finance",
            "erp",
            "oauth2",
            ("legal_entities", "coa", "ap", "ar", "journals", "projects"),
        ),
        FinanceProviderDefinition(
            "sap_s4hana",
            "erp",
            "oauth2",
            ("company_codes", "coa", "ap", "ar", "journals", "purchase_orders"),
        ),
        FinanceProviderDefinition(
            "sap_business_one",
            "erp",
            "session_token",
            ("coa", "business_partners", "ap", "ar", "journals"),
        ),
        FinanceProviderDefinition(
            "oracle_fusion_erp",
            "erp",
            "oauth2",
            ("ledgers", "coa", "ap", "ar", "journals", "procurement"),
        ),
        FinanceProviderDefinition(
            "acumatica",
            "erp",
            "oauth2",
            ("branches", "coa", "ap", "ar", "journals", "purchase_orders"),
        ),
        FinanceProviderDefinition(
            "odoo",
            "erp",
            "api_key",
            ("companies", "coa", "partners", "invoices", "bills", "journals"),
        ),
        FinanceProviderDefinition(
            "zoho_books",
            "accounting",
            "oauth2",
            ("coa", "contacts", "invoices", "bills", "payments"),
        ),
        FinanceProviderDefinition(
            "freshbooks", "accounting", "oauth2", ("clients", "invoices", "expenses", "payments")
        ),
        FinanceProviderDefinition(
            "wave", "accounting", "oauth2", ("accounts", "customers", "invoices", "transactions")
        ),
        FinanceProviderDefinition(
            "workday_financial_management",
            "erp",
            "oauth2",
            ("companies", "ledgers", "suppliers", "customers", "journals"),
        ),
        FinanceProviderDefinition(
            "epicor_kinetic",
            "erp",
            "api_key",
            ("companies", "coa", "ap", "ar", "journals", "purchase_orders"),
        ),
        FinanceProviderDefinition(
            "unit4_erpx", "erp", "oauth2", ("companies", "coa", "ap", "ar", "journals")
        ),
        FinanceProviderDefinition(
            "exact_online",
            "accounting",
            "oauth2",
            ("divisions", "coa", "contacts", "invoices", "journals"),
        ),
        FinanceProviderDefinition(
            "freeagent",
            "accounting",
            "oauth2",
            ("coa", "contacts", "invoices", "bills", "bank_transactions"),
        ),
        FinanceProviderDefinition(
            "bill_com",
            "ap_automation",
            "oauth2",
            ("vendors", "bills", "approvals", "payment_status"),
        ),
        FinanceProviderDefinition(
            "ramp",
            "spend_management",
            "oauth2",
            ("cards", "expenses", "reimbursements", "accounting_mappings"),
        ),
        FinanceProviderDefinition(
            "brex",
            "spend_management",
            "oauth2",
            ("cards", "expenses", "reimbursements", "transfers"),
        ),
        FinanceProviderDefinition(
            "airbase", "spend_management", "oauth2", ("cards", "expenses", "bills", "approvals")
        ),
        FinanceProviderDefinition(
            "expensify", "expense_management", "oauth2", ("expenses", "reports", "reimbursements")
        ),
        FinanceProviderDefinition(
            "sap_concur",
            "expense_management",
            "oauth2",
            ("expenses", "reports", "travel", "reimbursements"),
        ),
        FinanceProviderDefinition(
            "coupa",
            "procure_to_pay",
            "oauth2",
            ("suppliers", "purchase_orders", "invoices", "approvals"),
        ),
        FinanceProviderDefinition(
            "tipalti", "ap_automation", "oauth2", ("payees", "bills", "payment_status", "tax_forms")
        ),
        FinanceProviderDefinition(
            "avidxchange",
            "ap_automation",
            "partner_api",
            ("vendors", "invoices", "approvals", "payment_status"),
        ),
        FinanceProviderDefinition(
            "melio", "ap_automation", "partner_api", ("vendors", "bills", "payment_status")
        ),
        FinanceProviderDefinition(
            "modern_treasury",
            "treasury",
            "api_key",
            ("accounts", "payment_orders", "transactions", "ledger"),
        ),
        FinanceProviderDefinition(
            "treasury_prime",
            "banking_infrastructure",
            "oauth2",
            ("accounts", "transactions", "payments"),
        ),
        FinanceProviderDefinition(
            "kyriba",
            "treasury_management",
            "oauth2",
            ("cash_positions", "payments", "fx", "forecasting"),
        ),
        FinanceProviderDefinition(
            "gtreasury",
            "treasury_management",
            "api_key",
            ("cash_positions", "payments", "debt", "forecasting"),
        ),
        FinanceProviderDefinition(
            "highradius", "treasury_ar", "oauth2", ("cash_application", "receivables", "treasury")
        ),
        FinanceProviderDefinition(
            "trovata", "cash_management", "oauth2", ("accounts", "transactions", "cash_forecasts")
        ),
    )
}


def provider_codes() -> tuple[str, ...]:
    return tuple(sorted(PROVIDERS))
