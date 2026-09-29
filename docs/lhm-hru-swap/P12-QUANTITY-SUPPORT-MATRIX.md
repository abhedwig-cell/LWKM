# P12 quantity support matrix v1

This matrix distinguishes the product stage actually consumed by hrulist2SWAP.

| quantity | input read by P12 | observed aggregation | support interpretation |
|---|---|---|---|
| precipitation | meteo raster at SVAT coordinates | sum(value_i * area_i) / areawb_sum | spatial intensity; HRU area-weighted |
| evaporation | meteo raster at SVAT coordinates | sum(value_i * area_i) / areawb_sum | spatial intensity; HRU area-weighted |
| FLF | raw/decadal bdgflf_*_l1.idf from dirFilesflf | 100 * sum(value_i) / areawb_sum | MODFLOW budget-like extensive values converted to HRU depth; native time basis still to bind |
| QLAT | bdgqlat_*_l1.asc from dirFilesqlat | 100 * sum(value_i) / areawb_sum | derived coupling/balance product; upstream support depends on qmsw/uopp and MODFLOW terms |
| conductance qq | heads l1/l2 plus c1 per SVAT | 100 * mean((h2-h1)/c1) | resistance-derived intensity-like term; support must be checked |
| MetaSWAP climate products | processed outside P12 | source * uopp / 62500 before later use | SVAT intensity converted to MODFLOW-cell-equivalent intensity |

Precipitation and evaporation provide a clean reference implementation of area-weighted aggregation for intensive raster quantities in P12.

FLF intentionally follows a different algebra, consistent with an extensive MODFLOW budget term: sum first, divide by accounting area.

This difference should be preserved unless native-unit evidence contradicts it.
