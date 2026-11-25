import pytest

from flowforge.phase4e.router import status as s4e
from flowforge.phase4f.router import status as s4f
from flowforge.phase4g.router import status as s4g
from flowforge.phase4h.router import status as s4h
from flowforge.phase4i.router import status as s4i
from flowforge.phase4j.router import status as s4j


@pytest.mark.asyncio
@pytest.mark.parametrize("fn", [s4e, s4f, s4g, s4h, s4i, s4j])
async def test_status(fn) -> None:
    assert (await fn())["status"] == "implemented"
