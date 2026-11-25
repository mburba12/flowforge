from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommerceProviderDefinition:
    code: str
    family: str
    auth_model: str
    supports_webhooks: bool
    supports_marketplace: bool


PROVIDERS = {
    item.code: item
    for item in (
        CommerceProviderDefinition("shopify", "hosted_storefront", "oauth2", True, False),
        CommerceProviderDefinition(
            "woocommerce", "self_hosted_storefront", "api_keys", True, False
        ),
        CommerceProviderDefinition("bigcommerce", "hosted_storefront", "oauth2", True, False),
        CommerceProviderDefinition(
            "adobe_commerce", "enterprise_storefront", "oauth_or_token", True, False
        ),
        CommerceProviderDefinition(
            "salesforce_b2c_commerce", "enterprise_storefront", "oauth2", True, False
        ),
        CommerceProviderDefinition("commercetools", "headless_commerce", "oauth2", True, False),
        CommerceProviderDefinition("shopware", "self_hosted_storefront", "oauth2", True, False),
        CommerceProviderDefinition("prestashop", "self_hosted_storefront", "api_key", False, False),
        CommerceProviderDefinition("wix_stores", "hosted_storefront", "oauth2", True, False),
        CommerceProviderDefinition(
            "squarespace_commerce", "hosted_storefront", "oauth2", True, False
        ),
        CommerceProviderDefinition("ecwid", "hosted_storefront", "oauth2", True, False),
        CommerceProviderDefinition("lightspeed_ecom", "retail_commerce", "oauth2", True, False),
        CommerceProviderDefinition("medusa", "headless_commerce", "api_key", True, False),
        CommerceProviderDefinition("saleor", "headless_commerce", "token", True, False),
        CommerceProviderDefinition(
            "amazon_selling_partner", "marketplace", "oauth2_sigv4", True, True
        ),
        CommerceProviderDefinition("ebay_sell", "marketplace", "oauth2", True, True),
        CommerceProviderDefinition("etsy", "marketplace", "oauth2", True, True),
        CommerceProviderDefinition(
            "walmart_marketplace", "marketplace", "client_credentials", True, True
        ),
        CommerceProviderDefinition("tiktok_shop", "social_marketplace", "oauth2", True, True),
        CommerceProviderDefinition(
            "facebook_instagram_shops", "social_marketplace", "oauth2", True, True
        ),
        CommerceProviderDefinition(
            "google_merchant_center", "marketplace_feed", "oauth2", True, True
        ),
        CommerceProviderDefinition(
            "target_plus", "marketplace", "partner_credentials", False, True
        ),
        CommerceProviderDefinition("newegg_marketplace", "marketplace", "api_key", False, True),
        CommerceProviderDefinition("rakuten_marketplace", "marketplace", "api_key", False, True),
        CommerceProviderDefinition("mercadolibre", "marketplace", "oauth2", True, True),
        CommerceProviderDefinition("bol_com", "marketplace", "oauth2", False, True),
    )
}


def provider_codes() -> tuple[str, ...]:
    return tuple(sorted(PROVIDERS))
