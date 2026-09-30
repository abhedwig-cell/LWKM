# P12 MET sparse aggregation contract

The daily precipitation/ETref calculation is factored into two stages.

## Static stage

For each HRU and membership policy:
1. select source members;
2. map 250 m member coordinates to 1 km meteo pixels;
3. sum member active SVAT area (uopp) per meteo pixel;
4. normalize to weights summing exactly to 1.

Persist:
  hru, meteo_row, meteo_col, selected_uopp_m2, weight, membership_policy, source_hashes.

This mapping changes only when HRU membership, active SVAT area (uopp), selection policy or meteo grid geometry changes.

## Daily stage

For each daily raster:
  q_hru = sum(pixel_value * precomputed_weight)

No SVAT loop is required.

## Invariants

- weights per HRU sum to 1 within tolerance;
- all selected areas > 0;
- no selected member maps outside grid;
- NODATA under positive weight is fatal unless an explicit missing-data policy is configured;
- negative valid meteorological values are clipped only after NODATA masking, matching intended historical nonnegative forcing;
- source-current and donor-equal mappings are separate artifacts and never overwritten.

## Incremental regeneration

A changed daily precipitation raster invalidates only precipitation output for that date.
A changed daily ETref raster invalidates only ETref output for that date.
A changed HRU/membership/area mapping invalidates the static weights and all dependent daily aggregates.
District meteorology is independent of these grid weights.


## Area clarification

The sparse mapping is located through 250 m SVAT coordinates, but weights are NOT 62,500 m2 source-cell weights. The historical control binds area=BasicData/grids/uopp.asc. Therefore pixel weights are sums of selected uopp within each 1 km meteo pixel, normalized by total selected uopp.
