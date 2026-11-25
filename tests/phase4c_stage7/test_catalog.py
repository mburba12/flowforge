from flowforge.phase4c_stage7.catalog import PROVIDERS


def test_provider_coverage() -> None:
    required = {
        "salesforce_sales_cloud",
        "dynamics_365_sales",
        "hubspot_crm",
        "zoho_crm",
        "pipedrive",
        "zendesk",
        "intercom",
        "freshdesk",
        "servicenow_csm",
        "mailchimp",
        "klaviyo",
        "adobe_marketo_engage",
        "twilio",
        "microsoft_teams",
        "slack",
        "zoom",
        "ringcentral",
        "genesys_cloud",
    }
    assert required <= set(PROVIDERS)
    assert len(PROVIDERS) == 36
