from flowforge.phase4c_stage3.catalog import PROVIDERS


def test_provider_coverage() -> None:
    required = {
        "shopify",
        "woocommerce",
        "bigcommerce",
        "adobe_commerce",
        "salesforce_b2c_commerce",
        "commercetools",
        "shopware",
        "prestashop",
        "wix_stores",
        "squarespace_commerce",
        "amazon_selling_partner",
        "ebay_sell",
        "etsy",
        "walmart_marketplace",
        "tiktok_shop",
        "facebook_instagram_shops",
        "google_merchant_center",
        "medusa",
        "saleor",
    }
    assert required <= set(PROVIDERS)
    assert len(PROVIDERS) >= 25
