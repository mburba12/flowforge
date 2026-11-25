from flowforge.phase4c_stage4.catalog import PROVIDERS


def test_provider_coverage() -> None:
    required = {
        "pirate_ship",
        "ups",
        "fedex",
        "usps",
        "dhl_express",
        "canada_post",
        "royal_mail",
        "australia_post",
        "easypost",
        "shippo",
        "shipstation",
        "shipengine",
        "amazon_mcf",
        "amazon_fba",
        "walmart_fulfillment_services",
        "shipbob",
        "flexport",
        "maersk",
    }
    assert required <= set(PROVIDERS)
    assert len(PROVIDERS) >= 34
