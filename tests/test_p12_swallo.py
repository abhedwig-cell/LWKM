from tools.p12_swallo import (
    REALIZED_PRODUCTION_COMPAT,
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


def test_swallo_mode_is_explicit_and_default_preserves_supplied_source():
    assert swallo(3, 100, 11) == 1
    assert swallo(3, 100, 11, mode=SUPPLIED_SOURCE_V038) == 1
    assert swallo(3, 100, 11, mode=RUN2000_V027_COMPAT) == 3\n    assert swallo(3, 100, 11, mode=REALIZED_PRODUCTION_COMPAT) == 3


def test_run_2000_discriminating_inputs():
    # Independent recovered source indicator for HRU 2000 is 11.8204...
    # and realized INFRES3 is 725, so only the forced-system branch can
    # explain realized SWALLO3=3.
    indicator = 11.820416666666667
    assert swallo_supplied_source(3, 725, indicator) == 1
    assert swallo_realized_compat(3, 725, indicator) == 3
