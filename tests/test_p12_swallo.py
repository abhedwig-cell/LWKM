from tools.p12_swallo import (
    REALIZED_PRODUCTION_COMPAT,
    RUN2000_V027_COMPAT,
    SUPPLIED_SOURCE_V038,
    swallo,
    swallo_realized_compat,
    swallo_supplied_source,
)


def test_swallo_supplied_source_policy():
    assert swallo_supplied_source(1, 100, 11) == 1
    assert swallo_supplied_source(1, 100, 9.9) == 3
    assert swallo_supplied_source(1, 20001, 11) == 3
    assert swallo_supplied_source(3, 100, 11) == 1
    assert swallo_supplied_source(4, 100, 11) == 3


def test_swallo_run2000_v027_compat_forces_system_3():
    assert swallo_realized_compat(2, 100, 11) == 1
    assert swallo_realized_compat(3, 100, 11) == 3
    assert swallo_realized_compat(4, 100, 11) == 3
    assert REALIZED_PRODUCTION_COMPAT == RUN2000_V027_COMPAT


def test_swallo_mode_is_explicit_and_default_preserves_supplied_source():
    assert swallo(3, 100, 11) == 1
    assert swallo(3, 100, 11, mode=SUPPLIED_SOURCE_V038) == 1
    assert swallo(3, 100, 11, mode=RUN2000_V027_COMPAT) == 3
    assert swallo(3, 100, 11, mode=REALIZED_PRODUCTION_COMPAT) == 3


def test_run_2000_discriminating_inputs():
    indicator = 11.820416666666667
    assert swallo_supplied_source(3, 725, indicator) == 1
    assert swallo_realized_compat(3, 725, indicator) == 3
