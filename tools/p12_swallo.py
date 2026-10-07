"""Historical SWALLO policies with explicit provenance semantics."""

SUPPLIED_SOURCE_V038 = "SUPPLIED_SOURCE_V038"
RUN2000_V027_COMPAT = "RUN2000_V027_COMPAT"

# Backward-compatible alias. The 49-run oracle proves this is not a universal
# realized-production rule, so new code should use RUN2000_V027_COMPAT.
REALIZED_PRODUCTION_COMPAT = RUN2000_V027_COMPAT
MODERN_EXPLICIT_PHYSICAL = "MODERN_EXPLICIT_PHYSICAL"


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
    """Match the active supplied HRUlist2SWAP v0.38 source."""
    if int(system) > 3 or _common_forcing(infres_day, river_infiltration_indicator):
        return 3
    return 1


def swallo_run2000_v027_compat(
    system: int,
    infres_day: float,
    river_infiltration_indicator: float,
) -> int:
    """Match the run-2000 discriminator and v0.27 source-history statement.

    This mode is run-2000/v0.27 compatibility only. The recovered 49-run
    archive contains many system-3 SWALLO=1 cases and therefore falsifies
    a universal systems-3-5 forcing rule for that archive.
    """
    if int(system) > 2 or _common_forcing(infres_day, river_infiltration_indicator):
        return 3
    return 1


def swallo_realized_compat(
    system: int,
    infres_day: float,
    river_infiltration_indicator: float,
) -> int:
    """Backward-compatible wrapper for the run-2000/v0.27 mode."""
    return swallo_run2000_v027_compat(
        system,
        infres_day,
        river_infiltration_indicator,
    )


def swallo_modern_explicit(
    allow_infiltration: bool,
    infres_day: float,
    river_infiltration_indicator: float,
) -> int:
    """Modern production semantics independent of SWAP level number.

    A compressed SWAP level carries an explicit hydraulic capability.
    Drain-only levels are forced to SWALLO=3. Infiltration-capable levels
    remain eligible for SWALLO=1 unless the common resistance/indicator
    guards disable infiltration.
    """
    if (not bool(allow_infiltration)) or _common_forcing(
        infres_day,
        river_infiltration_indicator,
    ):
        return 3
    return 1


def swallo(
    system: int,
    infres_day: float,
    river_infiltration_indicator: float,
    *,
    mode: str = SUPPLIED_SOURCE_V038,
) -> int:
    """Evaluate SWALLO under an explicit provenance mode."""
    if mode == SUPPLIED_SOURCE_V038:
        return swallo_supplied_source(
            system,
            infres_day,
            river_infiltration_indicator,
        )
    if mode == RUN2000_V027_COMPAT:
        return swallo_run2000_v027_compat(
            system,
            infres_day,
            river_infiltration_indicator,
        )
    raise ValueError(f"unknown SWALLO mode: {mode}")
