from flowforge.phase4e.router import status


async def test_status() -> None:
    result = await status()
    assert result["status"] == "implemented"
    assert result["production_writes"] is False
