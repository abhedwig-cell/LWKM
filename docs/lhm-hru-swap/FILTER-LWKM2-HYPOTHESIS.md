# Preregistered hypothesis: filter_lwkm2

Status: hypothesis, not established fact.

Historical memory suggests filter_lwkm2 is nearly identical to filter_lwkm and that a very small number of cells may have been corrected because land-use information was zero/missing where a regular class was expected.

Do not encode this as production logic without raster evidence.

## Test

Compare filter_lwkm > 0 with historical islwkm/filter_lwkm2 cell-by-cell.

For every mismatch retain:
- SVAT id
- x/y
- direction: added or removed
- landgebruik22
- lu7, lu4, lu2
- bodem370

Report:
- positive count in both masks
- total mismatches
- added/removed counts
- number of mismatches with landgebruik22 == 0

## Interpretation

If all or most mismatches are LGN 0, inspect the source LGN/raster alignment before deciding whether filter_lwkm2 is a legitimate correction or a workaround for missing land-use data.

If exactly four mismatches are found, that supports the remembered historical incident but does not by itself establish its cause.

Target architecture should prefer an explicit SVAT-keyed correction relation over maintaining a second opaque domain raster.
