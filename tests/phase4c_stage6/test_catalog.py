from flowforge.phase4c_stage6.catalog import PROVIDERS


def test_provider_coverage() -> None:
    required = {
        "adp_workforce_now",
        "workday_hcm",
        "ukg_pro",
        "ukg_ready",
        "paychex_flex",
        "gusto",
        "rippling",
        "bamboohr",
        "dayforce",
        "paylocity",
        "paycom",
        "deel",
        "remote",
        "greenhouse",
        "lever",
        "deputy",
        "when_i_work",
    }
    assert required <= set(PROVIDERS)
    assert len(PROVIDERS) == 33
