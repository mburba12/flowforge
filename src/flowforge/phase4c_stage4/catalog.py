from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogisticsProviderDefinition:
    code: str
    family: str
    auth_model: str
    capabilities: tuple[str, ...]


PROVIDERS = {
    x.code: x
    for x in (
        LogisticsProviderDefinition(
            "ups", "parcel_carrier", "oauth2", ("rates", "labels", "tracking", "returns", "pickup")
        ),
        LogisticsProviderDefinition(
            "fedex",
            "parcel_carrier",
            "oauth2",
            ("rates", "labels", "tracking", "returns", "pickup"),
        ),
        LogisticsProviderDefinition(
            "usps", "postal_carrier", "oauth2", ("rates", "labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "dhl_express",
            "parcel_carrier",
            "api_key_secret",
            ("rates", "labels", "tracking", "customs"),
        ),
        LogisticsProviderDefinition(
            "dhl_parcel", "postal_carrier", "oauth2", ("labels", "tracking", "returns")
        ),
        LogisticsProviderDefinition(
            "canada_post", "postal_carrier", "api_key", ("rates", "labels", "tracking", "manifests")
        ),
        LogisticsProviderDefinition(
            "royal_mail", "postal_carrier", "oauth2", ("labels", "tracking", "manifests")
        ),
        LogisticsProviderDefinition(
            "australia_post", "postal_carrier", "api_key", ("rates", "labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "purolator", "parcel_carrier", "api_key", ("rates", "labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "ontrac", "last_mile_carrier", "api_key", ("rates", "labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "lasership", "last_mile_carrier", "api_key", ("labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "gls", "parcel_carrier", "api_key", ("rates", "labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "dpd", "parcel_carrier", "api_key", ("rates", "labels", "tracking", "returns")
        ),
        LogisticsProviderDefinition("postnl", "postal_carrier", "api_key", ("labels", "tracking")),
        LogisticsProviderDefinition(
            "postnord", "postal_carrier", "oauth2", ("labels", "tracking", "returns")
        ),
        LogisticsProviderDefinition(
            "sendle", "carbon_neutral_carrier", "api_key", ("rates", "labels", "tracking")
        ),
        LogisticsProviderDefinition(
            "easypost",
            "multi_carrier_platform",
            "api_key",
            ("rates", "labels", "tracking", "insurance", "returns"),
        ),
        LogisticsProviderDefinition(
            "shippo",
            "multi_carrier_platform",
            "oauth2_or_token",
            ("rates", "labels", "tracking", "customs", "returns"),
        ),
        LogisticsProviderDefinition(
            "shipstation",
            "multi_carrier_platform",
            "api_key",
            ("rates", "labels", "tracking", "manifests"),
        ),
        LogisticsProviderDefinition(
            "pirate_ship",
            "multi_carrier_platform",
            "partner_or_private_api",
            (
                "rates",
                "labels",
                "tracking",
                "returns",
            ),
        ),
        LogisticsProviderDefinition(
            "shipengine",
            "multi_carrier_platform",
            "api_key",
            ("rates", "labels", "tracking", "address_validation"),
        ),
        LogisticsProviderDefinition(
            "aftership", "visibility_platform", "api_key", ("tracking", "notifications")
        ),
        LogisticsProviderDefinition(
            "project44", "visibility_platform", "oauth2", ("tracking", "eta", "freight_visibility")
        ),
        LogisticsProviderDefinition(
            "amazon_mcf",
            "fulfillment_network",
            "oauth2_sigv4",
            ("fulfillment_orders", "tracking", "returns"),
        ),
        LogisticsProviderDefinition(
            "amazon_fba",
            "fulfillment_network",
            "oauth2_sigv4",
            ("inventory", "inbound", "fulfillment", "returns"),
        ),
        LogisticsProviderDefinition(
            "walmart_fulfillment_services",
            "fulfillment_network",
            "oauth2",
            ("inventory", "fulfillment", "tracking"),
        ),
        LogisticsProviderDefinition(
            "shipbob",
            "third_party_logistics",
            "oauth2",
            ("inventory", "fulfillment", "tracking", "returns"),
        ),
        LogisticsProviderDefinition(
            "flexport", "freight_forwarder", "oauth2", ("freight_booking", "tracking", "documents")
        ),
        LogisticsProviderDefinition(
            "ch_robinson",
            "third_party_logistics",
            "oauth2",
            ("freight_quotes", "labels", "tracking"),
        ),
        LogisticsProviderDefinition(
            "dsv", "freight_forwarder", "oauth2", ("freight_booking", "tracking")
        ),
        LogisticsProviderDefinition(
            "kuehne_nagel", "freight_forwarder", "oauth2", ("freight_booking", "tracking")
        ),
        LogisticsProviderDefinition(
            "maersk", "ocean_carrier", "oauth2", ("ocean_booking", "container_tracking")
        ),
        LogisticsProviderDefinition(
            "shipmonk",
            "third_party_logistics",
            "api_key",
            ("inventory", "fulfillment", "tracking", "returns"),
        ),
        LogisticsProviderDefinition(
            "red_stag", "third_party_logistics", "api_key", ("inventory", "fulfillment", "tracking")
        ),
    )
}


def provider_codes() -> tuple[str, ...]:
    return tuple(sorted(PROVIDERS))
