from flowforge.phase5b.release import REQUIRED_GATES, Gate, GateState, evaluate


def test_release():
    passed, missing = evaluate(
        tuple(Gate(n, GateState.PASSED, f"https://evidence/{n}") for n in REQUIRED_GATES)
    )
    assert passed and not missing


def test_missing():
    passed, missing = evaluate(())
    assert not passed and missing
