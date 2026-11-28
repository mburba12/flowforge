"""Small in-process rate limits for the public sign-in and sign-up endpoints.

The client address comes from CF-Connecting-IP (set by Cloudflare; the API and web
listen on 127.0.0.1 only, so public traffic always arrives through the tunnel), then
X-Forwarded-For, then the socket peer. One API process serves the system, so memory
is enough; limits reset when the API restarts.
"""

import time
from collections import deque
from threading import Lock

from fastapi import HTTPException, Request, status

_hits: dict[str, deque[float]] = {}
_lock = Lock()


def client_address(request: Request) -> str:
    for header in ("cf-connecting-ip", "x-forwarded-for"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()[:64]
    return request.client.host if request.client else "unknown"


def enabled() -> bool:
    """On in production (FLOWFORGE_RATE_LIMITS=on|off overrides; rehearsals turn it off)."""
    from flowforge.core.config import settings

    choice = settings.rate_limits.strip().lower()
    if choice in {"on", "true", "1", "yes"}:
        return True
    if choice in {"off", "false", "0", "no"}:
        return False
    return settings.env == "production"


def check(key: str, limit: int, window_seconds: int) -> None:
    """Count one attempt for key; refuse with 429 once limit is reached in the window."""
    if not enabled():
        return
    now = time.monotonic()
    with _lock:
        hits = _hits.setdefault(key, deque())
        while hits and now - hits[0] > window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            retry = int(window_seconds - (now - hits[0])) + 1
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many attempts. Please wait a few minutes and try again.",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)
        if len(_hits) > 50_000:  # keep memory bounded under abuse
            for stale in [k for k, v in _hits.items() if not v or now - v[-1] > 3600][:10_000]:
                _hits.pop(stale, None)


def reset() -> None:
    with _lock:
        _hits.clear()
