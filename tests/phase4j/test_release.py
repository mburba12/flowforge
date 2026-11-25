from flowforge.phase4j.release import REQUIRED_GATES, ReleaseGate, evaluate_release


def test_release_pass() -> None:
    passed, missing = evaluate_release(
        tuple(ReleaseGate(name, True, "e") for name in REQUIRED_GATES)
    )
    assert passed and not missing


def test_release_missing() -> None:
    passed, missing = evaluate_release((ReleaseGate("ruff", True, "e"),))
    assert not passed and "tests" in missing
