# 2018 MET grid source characterization

Supplied:
- PRECIPITATION_2018.zip
- EVAPORATION_2018.zip

## Raster contract

Both daily ASC families:
- 300 columns x 325 rows
- xllcorner 0 m
- yllcorner 300,000 m
- cell size 1,000 m
- extent 0..300,000 x 300,000..625,000 m
- NODATA -9999
- 365 daily ASC grids for 2018.

Precipitation observed valid range across 2018:
  0 .. 116.1249
mean of daily spatial means ≈ 1.7889.

Evaporation observed valid range:
  0.03185 .. 5.81984
mean of daily spatial means ≈ 1.8723.

These magnitudes are consistent with daily mm-scale meteorological quantities, but unit=mm/day should still be bound from producer metadata/control rather than inferred solely from magnitude.

EVAPORATION archive additionally contains 14 IDF files on selected dates. The ASC daily family is complete and is the direct format consumed by the current P12 meteo path when referenced by metegrid.

## Spatial relation to SVAT grid

Meteo resolution is 1 km, while source LHM/SVAT coordinates are on the 250 m grid. Thus up to 16 source cells share one meteo pixel.

P12 maps every member coordinate to its containing meteo pixel and computes area-weighted RAIN/ETref over selected members.

Because many members can share the same meteo value, a modern producer can optimize by aggregating selected representation area per meteo pixel first:
  sum_pixel(value_p * selected_area_p) / sum(selected_area_p)
rather than evaluating every member separately for every day.

This is algebraically identical and potentially much faster.

## Audit guards

- NODATA must never be clipped to zero by MAX(value,0). The current Fortran loops MAX over every grid cell after reading; correctness depends on readr4grid having already converted/handled novar values. Modern code must treat NODATA explicitly before nonnegative clipping.
- duplicate/missing dates must fail validation;
- evaporation archive has extra IDF artifacts; date inventory must be based on ASC family, not raw file count.
