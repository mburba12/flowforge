"""Outbound HTTP for provider APIs (one place to set timeouts; tests swap the transport)."""

from typing import Any

import httpx

# Tests set this to an httpx.MockTransport; None means real network access.
TRANSPORT: httpx.AsyncBaseTransport | None = None


class ProviderError(ValueError):
    """A provider refused or failed a request; the message is safe to show to users."""


def client(base_url: str = "", **kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(25.0, connect=10.0),
        transport=TRANSPORT,
        headers={"User-Agent": "KrovWorkAgent/1.0"},
        **kwargs,
    )


def json_or_error(response: httpx.Response, provider: str) -> Any:
    try:
        body = response.json()
    except ValueError:
        body = None
    if response.status_code >= 400:
        message = None
        if isinstance(body, dict):
            message = (
                body.get("display_message")
                or body.get("error_message")
                or body.get("message")
                or body.get("error_description")
                or body.get("detail")
            )
            errors = body.get("errors") or body.get("response", {}).get("errors")
            if not message and isinstance(errors, list) and errors:
                first = errors[0]
                message = first.get("message") if isinstance(first, dict) else str(first)
            if not message and isinstance(body.get("error"), str):
                message = body["error"]
        raise ProviderError(
            f"{provider} refused the request ({response.status_code}): "
            f"{str(message or response.reason_phrase)[:300]}"
        )
    return body


async def request(method: str, url: str, provider: str, **kwargs: Any) -> Any:
    try:
        async with client() as http:
            response = await http.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        raise ProviderError(f"Could not reach {provider}: {type(exc).__name__}") from exc
    return json_or_error(response, provider)
