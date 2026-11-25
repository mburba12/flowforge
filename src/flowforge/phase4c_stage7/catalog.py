from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EngagementProviderDefinition:
    code: str
    family: str
    auth_model: str
    capabilities: tuple[str, ...]


PROVIDERS = {
    item.code: item
    for item in (
        EngagementProviderDefinition(
            "salesforce_sales_cloud",
            "crm",
            "oauth2",
            ("contacts", "accounts", "leads", "opportunities", "activities"),
        ),
        EngagementProviderDefinition(
            "dynamics_365_sales",
            "crm",
            "oauth2",
            ("contacts", "accounts", "leads", "opportunities", "activities"),
        ),
        EngagementProviderDefinition(
            "hubspot_crm",
            "crm",
            "oauth2",
            ("contacts", "companies", "deals", "activities"),
        ),
        EngagementProviderDefinition(
            "zoho_crm", "crm", "oauth2", ("contacts", "accounts", "leads", "deals")
        ),
        EngagementProviderDefinition(
            "pipedrive",
            "crm",
            "oauth2",
            ("persons", "organizations", "deals", "activities"),
        ),
        EngagementProviderDefinition(
            "freshsales", "crm", "oauth2", ("contacts", "accounts", "leads", "deals")
        ),
        EngagementProviderDefinition(
            "monday_sales_crm",
            "crm",
            "oauth2",
            ("contacts", "accounts", "leads", "deals"),
        ),
        EngagementProviderDefinition(
            "copper",
            "crm",
            "oauth2",
            ("contacts", "companies", "opportunities", "activities"),
        ),
        EngagementProviderDefinition(
            "insightly",
            "crm",
            "api_key",
            ("contacts", "organizations", "opportunities", "projects"),
        ),
        EngagementProviderDefinition(
            "zendesk",
            "customer_support",
            "oauth2",
            ("users", "tickets", "comments", "sla"),
        ),
        EngagementProviderDefinition(
            "intercom",
            "customer_support",
            "oauth2",
            ("contacts", "conversations", "tickets", "articles"),
        ),
        EngagementProviderDefinition(
            "freshdesk",
            "customer_support",
            "oauth2",
            ("contacts", "tickets", "conversations", "sla"),
        ),
        EngagementProviderDefinition(
            "servicenow_csm",
            "customer_support",
            "oauth2",
            ("customers", "cases", "tasks", "sla"),
        ),
        EngagementProviderDefinition(
            "salesforce_service_cloud",
            "customer_support",
            "oauth2",
            ("contacts", "accounts", "cases", "entitlements"),
        ),
        EngagementProviderDefinition(
            "hubspot_service_hub",
            "customer_support",
            "oauth2",
            ("contacts", "tickets", "feedback", "activities"),
        ),
        EngagementProviderDefinition(
            "zoho_desk",
            "customer_support",
            "oauth2",
            ("contacts", "tickets", "comments", "sla"),
        ),
        EngagementProviderDefinition(
            "helpscout",
            "customer_support",
            "oauth2",
            ("customers", "conversations", "mailboxes"),
        ),
        EngagementProviderDefinition(
            "gorgias",
            "ecommerce_support",
            "oauth2",
            ("customers", "tickets", "messages"),
        ),
        EngagementProviderDefinition(
            "mailchimp",
            "marketing_automation",
            "oauth2",
            ("audiences", "campaigns", "engagement"),
        ),
        EngagementProviderDefinition(
            "klaviyo",
            "marketing_automation",
            "oauth2",
            ("profiles", "lists", "campaigns", "events"),
        ),
        EngagementProviderDefinition(
            "adobe_marketo_engage",
            "marketing_automation",
            "oauth2",
            ("leads", "lists", "campaigns", "activities"),
        ),
        EngagementProviderDefinition(
            "dynamics_365_customer_insights",
            "customer_data_marketing",
            "oauth2",
            ("profiles", "segments", "journeys", "events"),
        ),
        EngagementProviderDefinition(
            "salesforce_marketing_cloud",
            "marketing_automation",
            "oauth2",
            ("subscribers", "journeys", "campaigns", "events"),
        ),
        EngagementProviderDefinition(
            "braze",
            "customer_engagement",
            "api_key",
            ("users", "segments", "campaigns", "events"),
        ),
        EngagementProviderDefinition(
            "activecampaign",
            "marketing_automation",
            "oauth2",
            ("contacts", "lists", "campaigns", "automations"),
        ),
        EngagementProviderDefinition(
            "constant_contact",
            "marketing_automation",
            "oauth2",
            ("contacts", "lists", "campaigns", "engagement"),
        ),
        EngagementProviderDefinition(
            "twilio",
            "communications",
            "api_key",
            ("messages", "calls", "conversations", "delivery_events"),
        ),
        EngagementProviderDefinition(
            "microsoft_teams",
            "collaboration",
            "oauth2",
            ("teams", "channels", "messages", "meetings"),
        ),
        EngagementProviderDefinition(
            "slack",
            "collaboration",
            "oauth2",
            ("workspaces", "channels", "messages", "users"),
        ),
        EngagementProviderDefinition(
            "zoom",
            "communications",
            "oauth2",
            ("meetings", "webinars", "participants", "recording_metadata"),
        ),
        EngagementProviderDefinition(
            "ringcentral",
            "communications",
            "oauth2",
            ("messages", "calls", "meetings", "delivery_events"),
        ),
        EngagementProviderDefinition(
            "genesys_cloud",
            "contact_center",
            "oauth2",
            ("conversations", "queues", "agents", "quality"),
        ),
        EngagementProviderDefinition(
            "five9",
            "contact_center",
            "oauth2",
            ("calls", "campaigns", "agents", "dispositions"),
        ),
        EngagementProviderDefinition(
            "talkdesk",
            "contact_center",
            "oauth2",
            ("calls", "contacts", "agents", "dispositions"),
        ),
        EngagementProviderDefinition(
            "aircall",
            "communications",
            "oauth2",
            ("calls", "contacts", "users", "tags"),
        ),
        EngagementProviderDefinition(
            "dialpad",
            "communications",
            "oauth2",
            ("calls", "messages", "users", "transcript_metadata"),
        ),
    )
}


def provider_codes() -> tuple[str, ...]:
    return tuple(sorted(PROVIDERS))
