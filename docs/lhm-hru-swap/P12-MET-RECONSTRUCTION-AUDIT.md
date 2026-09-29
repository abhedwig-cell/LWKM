# P12 MET producer reconstruction and audit

## Realized architecture

Meteo output combines two distinct sources.

### Spatial grid fields
RAIN and ETref are read from daily precipitation/evaporation grids listed by metegrid.

For the selected water-balance membership:
  rain_HRU = sum(rain_i * area_i) / sum(area_i)
  etref_HRU = sum(etref_i * area_i) / sum(area_i)

Negative grid values are clipped to zero first.

This is a standard area-weighted aggregation of intensive fields and is mathematically correct if area_i is the intended active/representation area.

### District fields
RAD, Tmin, Tmax, HUM, WIND and WET are copied from one district time series chosen by:
  meteo_maj = MAJORITY(meteo_i)
over ALL HRU members.

Thus these variables are not spatially averaged.

## Critical audit points

1. WB membership provenance
The supplied current source uses its issvatwb relation for RAIN/ETref. Realized BBC evidence indicates the generating executable likely used donor-equal semantics. Realized .met files can independently test which membership was used.

2. District majority weighting
MAJORITY is by member count, not area. If source cells all represent equal 62,500 m2 MODFLOW cells this is equivalent to full-cell area majority. If meteo district should represent active uopp area, it is not equivalent.

Do not change until realized output and intended support are established.

3. District discontinuity
RAD/T/HUM/WIND/WET switch discretely at the majority district boundary while RAIN/ETref are spatially averaged. This is an intentional/historical hybrid but should be explicit in the new datamodel.

4. WET repair
If rain < 0.01:
  rain=0; WET=0.
Else if district WET < 0.01:
  WET=max(0.01, maximum WET across all districts that day).

This cross-district fallback is nonlocal and deserves explicit regression; it can import a wet-duration value from an unrelated district.

5. Date convention
metegrid day number is converted with +1 because SWAP has no day 0. Preserve as an explicit calendar transform and test leap years.

## Modern producer recommendation

Separate:
- met_grid_aggregate: RAIN, ETref;
- met_district_lookup: RAD, Tmin, Tmax, HUM, WIND, WET;
- wet_repair policy;
- renderer.

Do not regenerate unrelated district source files.
