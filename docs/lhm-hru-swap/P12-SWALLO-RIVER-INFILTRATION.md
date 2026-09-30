# P12 SWALLO / river-infiltration contract

## Independent river-infiltration input

HRUlist2SWAP reads:
`riv_infil = LHM_uitvoer/filter/Riv_infiltratie_1991-2020.asc`

Legacy aggregation:
`infil_avg = equal-member mean(riv_infil_i)`.

This is a long-term regional river/infiltration diagnostic from LHM output, not:
- a soil-hydraulic property;
- part of Piet's representative-soil identity;
- the drainage-system infiltration factor used in INFRES.

The same raster is written by LWKM_makeHRU to `SVAT_INFO_HRU.CSV`, but historically under the misleading header `wegzijgingz(mm/j)`.

For the current 10,242-HRU population:
- `infil_avg < 10`: 6,324 HRUs;
- `infil_avg >= 10`: 3,918 HRUs;
- exact equality at 10: 0.

## Common SWALLO conditions

Both recovered semantics use:
- `INFRES > 20000 -> SWALLO = 3`;
- `infil_avg < 10 -> SWALLO = 3`.

The threshold-10 provenance remains open documentation, but its source field and aggregation support are now bound.

## Provenance split for forced systems

The active supplied HRUlist2SWAP v0.38 source contains:
`system > 3`.

That implies:
- systems 4-5 forced to SWALLO=3;
- system 3 may remain SWALLO=1 when the other two conditions are false.

However:
- the source history comment for v0.27 states `SWALLO=3 voor sys>2`;
- realized run `2000.dra` has `SWALLO3=3`;
- run 2000 independently reconstructs `infil_avg = 11.8204166667`;
- realized `INFRES3 = 725`.

Therefore run 2000 discriminates the two rules. The active supplied-source `system > 3` branch predicts SWALLO3=1 and does not match the realized executable. The `system > 2` rule predicts SWALLO3=3 and does match.

Full evidence:
`P12-SWALLO-REALIZED-PROVENANCE-2026-09-30.md`.

## Explicit compatibility modes

Modern code must not silently collapse these histories.

`SUPPLIED_SOURCE_V038`
- force systems 4-5;
- exact active supplied-source behavior.

`REALIZED_PRODUCTION_COMPAT`
- force systems 3-5;
- consistent with run-2000 realized oracle and the v0.27 history statement.

Implementation:
`tools/p12_swallo.py`.

The default helper remains supplied-source mode for backward compatibility. Production/direct-renderer code must choose the intended provenance mode explicitly.

## Invariants

Do not:
- derive river infiltration from representative soil;
- substitute INFRES source factors for the separate river-infiltration indicator;
- change threshold 10 incidentally;
- describe the supplied-source and realized behaviors as identical.

Status:
**RIVER_INFILTRATION_SEMANTICS_BOUND; SWALLO_PROVENANCE_SPLIT_CONFIRMED**.
