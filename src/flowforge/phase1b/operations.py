from dataclasses import dataclass
from time import monotonic
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Health:
    status: str
    database: bool
    storage: bool


class HealthService:
    def readiness(self, database: bool, storage: bool) -> Health:
        return Health("ready" if database and storage else "degraded", database, storage)


def correlation_id(value: str | None = None) -> str:
    return value or str(uuid4())


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = monotonic()
        xs = [x for x in self.hits.get(key, []) if now - x < self.window]
        if len(xs) >= self.limit:
            self.hits[key] = xs
            return False
        xs.append(now)
        self.hits[key] = xs
        return True


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'",
}
