from flowforge.phase4g.router import status


async def test_status() -> None:
    result = await status()
    assert result["status"] == "implemented"
    assert result["production_writes"] is False
