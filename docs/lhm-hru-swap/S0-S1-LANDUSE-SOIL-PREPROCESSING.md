# S0/S1 land-use and soil preprocessing

## Confirmed consumer contract

LWKM_makeHRU v0.20 consumes these Basicdata grids directly:

Land use:
- lgn250.asc -> landgebruik22
- lu7.asc -> lu7
- lu4.asc -> lu4
- lu2.asc -> lu2

Soil:
- bodem.asc -> bodem370
- soil79.asc -> bofek79
- soil21.asc -> pawn21
- soil4.asc -> grondsoort4
- soil2.asc -> grondsoort2

LWKM_makeHRU does not derive these classes. The LHM filter/gridcalc batch audited so far also does not produce lu7/lu4/lu2 or soil79/soil21/soil4/soil2.

## Current reconstruction status

The original producer scripts/classification lookup files for these eight derived Basicdata grids have not been recovered from the supplied indexed source set.

However, SVAT_INFO.csv contains the realized source and derived values side-by-side for the full SVAT product:
- landgebruik22, lu7, lu4, lu2
- bodem370, bofek79, pawn21, grondsoort4, grondsoort2

Therefore the realized historical mapping can be recovered empirically and admitted only if each source class maps deterministically to exactly one derived tuple across the full table.

This is a different claim from recovering the original producer:
- REALIZED_MAPPING_EXACT: can be proven from the historical product.
- ORIGINAL_PRODUCER_EXACT: remains open until the old lookup/script is found.

## Required regression

For land use, group by landgebruik22 and require one unique tuple (lu7,lu4,lu2) per source code.

For soil, group by bodem370 and require one unique tuple (bofek79,pawn21,grondsoort4,grondsoort2) per source code.

Any ambiguity means the derived class depends on additional spatial/contextual information and cannot be represented by a one-column lookup.

The canonical target should store recovered mappings as small versioned tables and regenerate the derived columns directly, eliminating redundant raster intermediates when the deterministic hypothesis is confirmed.
