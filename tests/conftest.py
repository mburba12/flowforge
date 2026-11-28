"""Operation coverage: record which API operations answered with success during tests.

Set FLOWFORGE_OPERATION_COVERAGE=<file> to append one "METHOD module:function" line per
successful (2xx) call. tests/extended/operation_coverage.py merges these records with
the operation catalog and lists operations no test or audit has exercised successfully.
"""

import os
from typing import Any

COVERAGE_FILE = os.getenv("FLOWFORGE_OPERATION_COVERAGE")


def install_coverage_recorder(app: Any, path: str) -> None:
    from flowforge.platform.authorization import endpoint_key

    seen: set[str] = set()

    class Recorder:
        def __init__(self, app: Any) -> None:
            self.inner = app

        async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
            if scope.get("type") != "http":
                await self.inner(scope, receive, send)
                return
            status: dict[str, int] = {}

            async def capture(message: Any) -> None:
                if message.get("type") == "http.response.start":
                    status["code"] = message["status"]
                await send(message)

            await self.inner(scope, receive, capture)
            endpoint = scope.get("endpoint")
            if endpoint is not None and 200 <= status.get("code", 0) < 300:
                line = f"{scope['method']} {endpoint_key(endpoint)}"
                if line not in seen:
                    seen.add(line)
                    with open(path, "a", encoding="utf-8") as handle:
                        handle.write(line + "\n")

    app.add_middleware(Recorder)  # type: ignore[arg-type]


if COVERAGE_FILE:
    from flowforge.main import app as _app

    install_coverage_recorder(_app, COVERAGE_FILE)
