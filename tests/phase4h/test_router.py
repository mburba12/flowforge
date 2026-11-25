from flowforge.phase4h.router import status


async def test_status() -> None:
    result = await status()
    assert result["status"] == "implemented"
    assert result["production_writes"] is False
