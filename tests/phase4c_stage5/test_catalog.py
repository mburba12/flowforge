from flowforge.phase4c_stage5.catalog import PROVIDERS


def test_provider_coverage() -> None:
    required = {
        "quickbooks_online",
        "quickbooks_desktop",
        "xero",
        "sage_intacct",
        "netsuite",
        "dynamics_365_business_central",
        "dynamics_365_finance",
        "sap_s4hana",
        "oracle_fusion_erp",
        "acumatica",
        "odoo",
        "zoho_books",
        "bill_com",
        "ramp",
        "brex",
        "expensify",
        "sap_concur",
        "coupa",
        "tipalti",
        "modern_treasury",
        "treasury_prime",
        "kyriba",
    }
    assert required <= set(PROVIDERS)
    assert len(PROVIDERS) >= 35
