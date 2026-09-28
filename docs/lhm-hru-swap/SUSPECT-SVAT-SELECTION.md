# Verdachte SVATs - reconstructed selection authority

Status: source-reconstructed; full raster regression pending.

The historical suspicious-cell set is not created by LWKM_makeHRU itself. The Fortran program consumes eight precomputed selection grids. Their producer is the gridcalc workflow.

## Selection criteria

| flag | producer condition | scope/exceptions |
|---|---|---|
| ghg_sel | ghg < 0 | agriculture |
| gt1_sel | glg < 50 | agriculture, excluding peat grass |
| gt2_sel | ghg < 40 and 50 <= glg < 80 | agriculture excluding grass; special exclusions for bulbs and tree cultivation |
| gt8_sel | kwelwegz > 1 and GT > 7 | GT8 only |
| kwel_sel | kwelwegz > 1826 nature; > 730 agriculture | exclude polders |
| wegzijging_sel | kwelwegz < -548 | LWKM domain, exclude polders |
| runoff_sel | runoff < -548 nature; < -183 agriculture | historical runoff sign is negative |
| subinfil_sel | ontw_netto > 365 | LWKM domain, exclude polders |

Historical producer values 183/365/548/730/1826 are thresholds in the source grid convention. Comments associate them with approximately 0.5/1/1.5/2/5 mm/day, but compatibility code must preserve producer values until unit conversion is independently verified.

ontw_netto is produced upstream as runoff + rivdrn_netto.

## Land-use masks

Agriculture mask uses LGN classes 0,1,2,3,4,5,6,7,9,10,21 within filter_lwkm.

Agriculture-without-grass uses 0,2,3,4,5,6,7,9,10,21.

Peat grass is LGN 1 with BOFEK 1..18.

Bulb and tree-cultivation GT2 exclusions are derived from the same GHG/GLG GT2 window, with LGN 10 for bulbs and LGN 7 + BOFEK 1..18 for tree cultivation.

## Consumer semantics

LWKM_makeHRU clips each input flag at zero and marks a SVAT suspicious when any flag is positive. It additionally writes a diagnostic decimal code containing the flag families.

Historical union regression target: 20,934 SVATs.

## Version caveat

The producer batch contains an older selection block plus a later block explicitly labelled "Selection rules agreed in Oct-2025". Six flags are overwritten by the later block. GT1 and GT2 are not recreated there and therefore originate from the earlier block.

The current Python compatibility implementation reflects this mixed provenance. It must be compared against the eight realized historical selection grids before HISTORICAL_EXACT admission.

## New workflow

Raw producer variables -> derive eight flags -> compare with historical flags -> qualification table -> HRU clustering.

Historical flags are regression evidence, not required scientific input in the target architecture.
