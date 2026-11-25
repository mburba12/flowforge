from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkforceProviderDefinition:
    code: str
    family: str
    auth_model: str
    capabilities: tuple[str, ...]


PROVIDERS = {
    item.code: item
    for item in (
        WorkforceProviderDefinition(
            "adp_workforce_now",
            "hcm_payroll",
            "oauth2",
            ("workers", "payroll", "benefits", "time"),
        ),
        WorkforceProviderDefinition(
            "adp_run", "smb_payroll", "oauth2", ("workers", "payroll", "tax_forms")
        ),
        WorkforceProviderDefinition(
            "workday_hcm",
            "enterprise_hcm",
            "oauth2",
            ("workers", "jobs", "compensation", "benefits", "payroll"),
        ),
        WorkforceProviderDefinition(
            "ukg_pro",
            "enterprise_hcm",
            "oauth2",
            ("workers", "payroll", "time", "benefits"),
        ),
        WorkforceProviderDefinition(
            "ukg_ready",
            "midmarket_hcm",
            "oauth2",
            ("workers", "payroll", "time", "scheduling"),
        ),
        WorkforceProviderDefinition(
            "paychex_flex",
            "hcm_payroll",
            "oauth2",
            ("workers", "payroll", "benefits", "time"),
        ),
        WorkforceProviderDefinition(
            "gusto",
            "smb_payroll",
            "oauth2",
            ("workers", "payroll", "benefits", "contractors"),
        ),
        WorkforceProviderDefinition(
            "rippling",
            "workforce_platform",
            "oauth2",
            ("workers", "payroll", "benefits", "time", "devices"),
        ),
        WorkforceProviderDefinition(
            "bamboohr", "hris", "api_key", ("workers", "jobs", "time_off", "documents")
        ),
        WorkforceProviderDefinition(
            "dayforce",
            "enterprise_hcm",
            "oauth2",
            ("workers", "payroll", "time", "benefits", "scheduling"),
        ),
        WorkforceProviderDefinition(
            "paylocity",
            "hcm_payroll",
            "oauth2",
            ("workers", "payroll", "time", "benefits"),
        ),
        WorkforceProviderDefinition(
            "paycom",
            "hcm_payroll",
            "partner_api",
            ("workers", "payroll", "time", "benefits"),
        ),
        WorkforceProviderDefinition(
            "square_payroll", "smb_payroll", "oauth2", ("workers", "payroll", "time")
        ),
        WorkforceProviderDefinition(
            "quickbooks_payroll",
            "smb_payroll",
            "oauth2",
            ("workers", "payroll", "tax_forms"),
        ),
        WorkforceProviderDefinition(
            "deel",
            "global_workforce",
            "oauth2",
            ("workers", "global_payroll", "contractors", "eor"),
        ),
        WorkforceProviderDefinition(
            "remote",
            "global_workforce",
            "oauth2",
            ("workers", "global_payroll", "contractors", "eor"),
        ),
        WorkforceProviderDefinition(
            "justworks",
            "peo",
            "partner_api",
            ("workers", "payroll", "benefits", "compliance"),
        ),
        WorkforceProviderDefinition(
            "trinet",
            "peo",
            "partner_api",
            ("workers", "payroll", "benefits", "compliance"),
        ),
        WorkforceProviderDefinition(
            "papaya_global",
            "global_payroll",
            "oauth2",
            ("workers", "global_payroll", "payments"),
        ),
        WorkforceProviderDefinition(
            "velocity_global",
            "global_workforce",
            "partner_api",
            ("workers", "global_payroll", "eor"),
        ),
        WorkforceProviderDefinition(
            "greenhouse", "ats", "api_key", ("candidates", "jobs", "offers", "hires")
        ),
        WorkforceProviderDefinition(
            "lever", "ats", "api_key", ("candidates", "jobs", "offers", "hires")
        ),
        WorkforceProviderDefinition(
            "icims", "ats", "oauth2", ("candidates", "jobs", "offers", "hires")
        ),
        WorkforceProviderDefinition(
            "workable", "ats", "api_key", ("candidates", "jobs", "offers", "hires")
        ),
        WorkforceProviderDefinition(
            "deputy",
            "workforce_management",
            "oauth2",
            ("workers", "schedules", "time", "leave"),
        ),
        WorkforceProviderDefinition(
            "when_i_work",
            "workforce_management",
            "oauth2",
            ("workers", "schedules", "time"),
        ),
        WorkforceProviderDefinition(
            "homebase",
            "workforce_management",
            "oauth2",
            ("workers", "schedules", "time", "payroll"),
        ),
        WorkforceProviderDefinition(
            "7shifts",
            "workforce_management",
            "oauth2",
            ("workers", "schedules", "time"),
        ),
        WorkforceProviderDefinition(
            "benefitfocus",
            "benefits",
            "partner_api",
            ("workers", "enrollments", "plans"),
        ),
        WorkforceProviderDefinition(
            "bswift", "benefits", "partner_api", ("workers", "enrollments", "plans")
        ),
        WorkforceProviderDefinition(
            "employee_navigator",
            "benefits",
            "partner_api",
            ("workers", "enrollments", "plans"),
        ),
        WorkforceProviderDefinition(
            "guideline",
            "retirement",
            "partner_api",
            ("workers", "contributions", "plans"),
        ),
        WorkforceProviderDefinition(
            "human_interest",
            "retirement",
            "partner_api",
            ("workers", "contributions", "plans"),
        ),
    )
}


def provider_codes() -> tuple[str, ...]:
    return tuple(sorted(PROVIDERS))
