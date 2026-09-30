"""Historical SWALLO policies with explicit provenance semantics."""

SUPPLIED_SOURCE_V038 = "SUPPLIED_SOURCE_V038"
REALIZED_PRODUCTION_COMPAT = "REALIZED_PRODUCTION_COMPAT"


def _common_forcing(infres_day: float, river_infiltration_indicator: float) -> bool:
    return (
        float(infres_day) > 20000.0
        or float(river_infiltration_indicator) < 10.0
    )


def swallo_supplied_source(
    system: int,
    infres_day: float,
    river_infiltration_indicator: float,
) -> int:
    """Match the active supplied HRUlist2SWAP v0.38 source.

    The supplied source forces systems 4-5 by the explicit system > 3 branch.
    """
    if int(system) > 3 or _common_forcing(infres_day, river_infiltration_indicator):
        return 3
    return 1


def swallo_realized_compat(
    system: int,
    infres_day: float,
    river_infiltration_indicator: float,
) -> int:
    """Match the run-2000 realized oracle and v0.27 source-history statement.

    The realized run-2000 system-3 row discriminates this from the active
    supplied-source rule: INFRES3 is below 20000, the independent river
    infiltration indicator is above 10, yet SWALLO3 is 3.
    """
    if int(system) > 2 or _common_forcing(infres_day, river_infiltration_indicator):
        return 3
    return 1


def swallo(
    system: int,
    infres_day: float,
    river_infiltration_indicator: float,
    *,
    mode: str = SUPPLIED_SOURCE_V038,
) -> int:
    """Evaluate SWALLO under an explicit provenance mode.

    The default remains the supplied-source behavior for backward compatibility.
    Callers targeting realized production compatibility must opt in explicitly.
    """
    if mode == SUPPLIED_SOURCE_V038:
        return swallo_supplied_source(system, infres_day, river_infiltration_indicator)
    if mode == REALIZED_PRODUCTION_COMPAT:
        return swallo_realized_compat(system, infres_day, river_infiltration_indicator)
    raise ValueError(f"unknown SWALLO mode: {mode}")
