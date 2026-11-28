"""Carrier tracking adapters: FedEx, UPS, USPS and DHL (their official REST APIs), plus a
demo carrier with sample data.

Each business connects its own carrier developer credentials (FedEx Developer Portal,
UPS Developer Kit, USPS Web Tools APIs, DHL API Developer Portal). Every adapter returns
the same normalized result, so screens show one status vocabulary:
label_created, in_transit, out_for_delivery, delivered, exception, unknown.
"""

import base64
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

from .http import ProviderError, request


@dataclass(slots=True)
class TrackingResult:
    status: str
    detail: str | None = None
    estimated_delivery: date | None = None
    delivered_at: datetime | None = None
    location: str | None = None
    last_event_at: datetime | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CarrierField:
    name: str
    label: str
    secret: bool = False
    required: bool = True
    help: str = ""


@dataclass(frozen=True, slots=True)
class CarrierInfo:
    code: str
    name: str
    signup_url: str
    fields: tuple[CarrierField, ...]
    instructions: str


_ENV = CarrierField(
    "environment",
    "Environment (production or sandbox)",
    required=False,
    help="Use sandbox only with test credentials.",
)

CARRIERS: dict[str, CarrierInfo] = {
    "fedex": CarrierInfo(
        "fedex",
        "FedEx",
        "https://developer.fedex.com",
        (
            CarrierField("client_id", "API key"),
            CarrierField("client_secret", "Secret key", secret=True),
            CarrierField("account_number", "FedEx account number", required=False),
            _ENV,
        ),
        "In the FedEx Developer Portal, create a project with the Track API, then copy its API key and secret key.",
    ),
    "ups": CarrierInfo(
        "ups",
        "UPS",
        "https://developer.ups.com",
        (
            CarrierField("client_id", "Client ID"),
            CarrierField("client_secret", "Client secret", secret=True),
            CarrierField("account_number", "UPS account number", required=False),
            _ENV,
        ),
        "In the UPS Developer Portal, create an app with the Tracking product, then copy its client ID and secret.",
    ),
    "usps": CarrierInfo(
        "usps",
        "USPS",
        "https://developers.usps.com",
        (
            CarrierField("client_id", "Consumer key"),
            CarrierField("client_secret", "Consumer secret", secret=True),
            _ENV,
        ),
        "In the USPS Developer Portal, create an app with the Tracking API, then copy its consumer key and secret.",
    ),
    "dhl": CarrierInfo(
        "dhl",
        "DHL",
        "https://developer.dhl.com",
        (CarrierField("api_key", "API key", secret=True),),
        "In the DHL API Developer Portal, subscribe an app to Shipment Tracking - Unified and copy its API key.",
    ),
    "demo": CarrierInfo(
        "demo",
        "Demo carrier (sample data)",
        "",
        (),
        "Sample tracking data to try FlowForge. Tracking numbers start with DEMO.",
    ),
}


def detect_carrier(tracking_number: str) -> str | None:
    n = re.sub(r"\s", "", tracking_number).upper()
    if n.startswith("DEMO"):
        return "demo"
    if re.fullmatch(r"1Z[0-9A-Z]{16}", n) or re.fullmatch(r"(T\d{10}|K\d{10})", n):
        return "ups"
    if re.fullmatch(r"(94|93|92|95|82)\d{18,20}", n) or re.fullmatch(r"[A-Z]{2}\d{9}US", n):
        return "usps"
    if re.fullmatch(r"(\d{12}|\d{15}|\d{20}|96\d{20}|\d{22})", n):
        return "fedex"
    if re.fullmatch(r"(\d{10}|JJD\d{10,}|JVGL\d{10,}|[A-Z]{3}\d{7})", n):
        return "dhl"
    return None


def normalize_number(tracking_number: str) -> str:
    return re.sub(r"\s", "", tracking_number).upper()


def _place(*parts: Any) -> str | None:
    text = ", ".join(str(p) for p in parts if p)
    return text or None


def _dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _date(value: Any) -> date | None:
    moment = _dt(value)
    if moment:
        return moment.date()
    try:
        return datetime.strptime(str(value)[:8], "%Y%m%d").date() if value else None
    except ValueError:
        return None


def _finish(
    events: list[dict[str, Any]],
    status: str,
    detail: str | None,
    estimated: date | None,
    delivered: datetime | None,
) -> TrackingResult:
    events.sort(key=lambda e: e.get("at") or "", reverse=True)
    latest = events[0] if events else {}
    if status == "delivered" and delivered is None:
        delivered = _dt(latest.get("at"))
    return TrackingResult(
        status,
        detail or latest.get("description"),
        estimated,
        delivered,
        latest.get("location"),
        _dt(latest.get("at")),
        events[:60],
    )


# ------------------------------------------------------------------ FedEx
_FEDEX_STATUS = {
    "DL": "delivered",
    "OD": "out_for_delivery",
    "OC": "label_created",
    "DE": "exception",
    "SE": "exception",
    "CA": "exception",
    "RS": "exception",
    "DY": "exception",
    "HL": "in_transit",
}


async def _fedex(creds: dict[str, str], number: str) -> TrackingResult:
    host = (
        "https://apis-sandbox.fedex.com"
        if creds.get("environment") == "sandbox"
        else "https://apis.fedex.com"
    )
    token = await request(
        "POST",
        f"{host}/oauth/token",
        "FedEx",
        data={
            "grant_type": "client_credentials",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
        },
    )
    body = await request(
        "POST",
        f"{host}/track/v1/trackingnumbers",
        "FedEx",
        headers={"Authorization": f"Bearer {token['access_token']}", "X-locale": "en_US"},
        json={
            "includeDetailedScans": True,
            "trackingInfo": [{"trackingNumberInfo": {"trackingNumber": number}}],
        },
    )
    try:
        result = body["output"]["completeTrackResults"][0]["trackResults"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("FedEx returned no tracking information") from exc
    if result.get("error"):
        raise ProviderError(f"FedEx: {result['error'].get('message', 'tracking number not found')}")
    latest = result.get("latestStatusDetail") or {}
    code = latest.get("code") or latest.get("derivedCode") or ""
    status = _FEDEX_STATUS.get(code, "in_transit" if code else "unknown")
    events = [
        {
            "at": e.get("date"),
            "description": e.get("eventDescription"),
            "location": _place(
                (e.get("scanLocation") or {}).get("city"),
                (e.get("scanLocation") or {}).get("stateOrProvinceCode"),
                (e.get("scanLocation") or {}).get("countryCode"),
            ),
            "code": e.get("eventType"),
        }
        for e in result.get("scanEvents", [])
    ]
    times = {d.get("type"): d.get("dateTime") for d in result.get("dateAndTimes", [])}
    window = ((result.get("estimatedDeliveryTimeWindow") or {}).get("window") or {}).get("ends")
    return _finish(
        events,
        status,
        latest.get("description"),
        _date(times.get("ESTIMATED_DELIVERY") or window),
        _dt(times.get("ACTUAL_DELIVERY")),
    )


# ------------------------------------------------------------------ UPS
_UPS_STATUS = {
    "D": "delivered",
    "I": "in_transit",
    "M": "label_created",
    "MV": "label_created",
    "P": "in_transit",
    "X": "exception",
    "RS": "exception",
    "O": "out_for_delivery",
    "DO": "out_for_delivery",
    "NA": "unknown",
}


async def _ups(creds: dict[str, str], number: str) -> TrackingResult:
    host = (
        "https://wwwcie.ups.com"
        if creds.get("environment") == "sandbox"
        else "https://onlinetools.ups.com"
    )
    basic = base64.b64encode(f"{creds['client_id']}:{creds['client_secret']}".encode()).decode()
    token = await request(
        "POST",
        f"{host}/security/v1/oauth/token",
        "UPS",
        headers={"Authorization": f"Basic {basic}"},
        data={"grant_type": "client_credentials"},
    )
    body = await request(
        "GET",
        f"{host}/api/track/v1/details/{number}",
        "UPS",
        params={"locale": "en_US", "returnSignature": "false"},
        headers={
            "Authorization": f"Bearer {token['access_token']}",
            "transId": uuid4().hex[:32],
            "transactionSrc": "flowforge",
        },
    )
    try:
        package = body["trackResponse"]["shipment"][0]["package"][0]
    except (KeyError, IndexError, TypeError) as exc:
        warnings = (((body or {}).get("trackResponse") or {}).get("shipment") or [{}])[0].get(
            "warnings"
        )
        message = warnings[0].get("message") if warnings else "tracking number not found"
        raise ProviderError(f"UPS: {message}") from exc
    current = package.get("currentStatus") or {}
    events = []
    for a in package.get("activity", []):
        stamp = None
        if a.get("date"):
            t = (a.get("time") or "000000").ljust(6, "0")
            stamp = (
                f"{a['date'][:4]}-{a['date'][4:6]}-{a['date'][6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}+00:00"
            )
        address = ((a.get("location") or {}).get("address")) or {}
        events.append(
            {
                "at": stamp,
                "description": (a.get("status") or {}).get("description"),
                "location": _place(
                    address.get("city"), address.get("stateProvince"), address.get("country")
                ),
                "code": (a.get("status") or {}).get("type"),
            }
        )
    latest_type = ((package.get("activity") or [{}])[0].get("status") or {}).get("type", "")
    status = _UPS_STATUS.get(
        current.get("code", ""), _UPS_STATUS.get(latest_type, "in_transit" if events else "unknown")
    )
    if "out for delivery" in str(current.get("description", "")).lower():
        status = "out_for_delivery"
    estimated = next(
        (
            _date(d.get("date"))
            for d in package.get("deliveryDate", [])
            if d.get("type") in ("SDD", "RDD", "EDD")
        ),
        None,
    )
    delivered = next(
        (_date(d.get("date")) for d in package.get("deliveryDate", []) if d.get("type") == "DEL"),
        None,
    )
    return _finish(
        events,
        status,
        current.get("description"),
        estimated,
        datetime(delivered.year, delivered.month, delivered.day, tzinfo=UTC) if delivered else None,
    )


# ------------------------------------------------------------------ USPS
_USPS_STATUS = {
    "delivered": "delivered",
    "out for delivery": "out_for_delivery",
    "in transit": "in_transit",
    "pre-shipment": "label_created",
    "alert": "exception",
    "accepted": "in_transit",
    "available for pickup": "out_for_delivery",
    "delivery attempt": "exception",
    "return to sender": "exception",
}


async def _usps(creds: dict[str, str], number: str) -> TrackingResult:
    host = (
        "https://apis-tem.usps.com"
        if creds.get("environment") == "sandbox"
        else "https://apis.usps.com"
    )
    token = await request(
        "POST",
        f"{host}/oauth2/v3/token",
        "USPS",
        json={
            "grant_type": "client_credentials",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
        },
    )
    body = await request(
        "GET",
        f"{host}/tracking/v3/tracking/{number}",
        "USPS",
        params={"expand": "DETAIL"},
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    category = str(body.get("statusCategory") or body.get("status") or "").lower()
    status = next(
        (v for k, v in _USPS_STATUS.items() if k in category),
        "in_transit" if category else "unknown",
    )
    events = [
        {
            "at": e.get("eventTimestamp") or e.get("GMTTimestamp"),
            "description": e.get("eventType"),
            "location": _place(e.get("eventCity"), e.get("eventState"), e.get("eventCountry")),
            "code": e.get("eventCode"),
        }
        for e in body.get("trackingEvents", [])
    ]
    return _finish(
        events,
        status,
        body.get("statusSummary") or body.get("status"),
        _date(body.get("expectedDeliveryDate") or body.get("expectedDeliveryTimeStamp")),
        None,
    )


# ------------------------------------------------------------------ DHL
_DHL_STATUS = {
    "pre-transit": "label_created",
    "transit": "in_transit",
    "delivered": "delivered",
    "failure": "exception",
    "unknown": "unknown",
}


async def _dhl(creds: dict[str, str], number: str) -> TrackingResult:
    body = await request(
        "GET",
        "https://api-eu.dhl.com/track/shipments",
        "DHL",
        params={"trackingNumber": number},
        headers={"DHL-API-Key": creds["api_key"]},
    )
    try:
        shipment = body["shipments"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("DHL returned no tracking information") from exc
    current = shipment.get("status") or {}
    status = _DHL_STATUS.get(current.get("statusCode", ""), "unknown")
    if "out for delivery" in str(current.get("description", "")).lower():
        status = "out_for_delivery"
    events = [
        {
            "at": e.get("timestamp"),
            "description": e.get("description") or e.get("status"),
            "location": ((e.get("location") or {}).get("address") or {}).get("addressLocality"),
            "code": e.get("statusCode"),
        }
        for e in shipment.get("events", [])
    ]
    return _finish(
        events,
        status,
        current.get("description") or current.get("status"),
        _date(shipment.get("estimatedTimeOfDelivery")),
        None,
    )


# ------------------------------------------------------------------ demo
async def _demo(
    creds: dict[str, str], number: str, added: datetime | None = None
) -> TrackingResult:
    start = added or datetime.now(UTC)
    elapsed = (datetime.now(UTC) - start).total_seconds() / 3600
    stages = [
        (0, "label_created", "Label created", "Columbus, OH"),
        (0.01, "in_transit", "Picked up", "Columbus, OH"),
        (6, "in_transit", "Arrived at sort facility", "Indianapolis, IN"),
        (24, "out_for_delivery", "Out for delivery", "Chicago, IL"),
        (30, "delivered", "Delivered — front door", "Chicago, IL"),
    ]
    if number.endswith("X"):
        stages[3] = (24, "exception", "Delivery exception — address issue", "Chicago, IL")
        stages = stages[:4]
    reached = [s for s in stages if elapsed >= s[0]] or stages[:1]
    events = [
        {
            "at": (start + timedelta(hours=h)).isoformat(),
            "description": text,
            "location": where,
            "code": code,
        }
        for h, code, text, where in reached
    ]
    status = reached[-1][1]
    return _finish(
        events,
        status,
        reached[-1][2],
        (start + timedelta(hours=30)).date(),
        start + timedelta(hours=30) if status == "delivered" else None,
    )


ADAPTERS = {"fedex": _fedex, "ups": _ups, "usps": _usps, "dhl": _dhl}


async def track(
    carrier: str, creds: dict[str, str], number: str, added: datetime | None = None
) -> TrackingResult:
    if carrier == "demo":
        return await _demo(creds, number, added)
    adapter = ADAPTERS.get(carrier)
    if adapter is None:
        raise ValueError("Unsupported carrier")
    return await adapter(creds, number)


async def verify(carrier: str, creds: dict[str, str]) -> None:
    """Check credentials by signing in to the carrier (no shipment needed)."""
    info = CARRIERS[carrier]
    for f in info.fields:
        if f.required and not str(creds.get(f.name, "")).strip():
            raise ValueError(f"{info.name}: {f.label} is required")
    sandbox = creds.get("environment") == "sandbox"
    if carrier == "fedex":
        host = "https://apis-sandbox.fedex.com" if sandbox else "https://apis.fedex.com"
        await request(
            "POST",
            f"{host}/oauth/token",
            "FedEx",
            data={
                "grant_type": "client_credentials",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
            },
        )
    elif carrier == "ups":
        host = "https://wwwcie.ups.com" if sandbox else "https://onlinetools.ups.com"
        basic = base64.b64encode(f"{creds['client_id']}:{creds['client_secret']}".encode()).decode()
        await request(
            "POST",
            f"{host}/security/v1/oauth/token",
            "UPS",
            headers={"Authorization": f"Basic {basic}"},
            data={"grant_type": "client_credentials"},
        )
    elif carrier == "usps":
        host = "https://apis-tem.usps.com" if sandbox else "https://apis.usps.com"
        await request(
            "POST",
            f"{host}/oauth2/v3/token",
            "USPS",
            json={
                "grant_type": "client_credentials",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
            },
        )
    elif carrier == "dhl":
        try:
            await request(
                "GET",
                "https://api-eu.dhl.com/track/shipments",
                "DHL",
                params={"trackingNumber": "0000000000"},
                headers={"DHL-API-Key": creds["api_key"]},
            )
        except ProviderError as exc:
            if "(404)" not in str(exc):  # 404 = key accepted, number unknown
                raise
