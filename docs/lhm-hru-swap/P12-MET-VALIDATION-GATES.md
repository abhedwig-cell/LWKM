# P12 MET validation gates

## District oracle gate

For each supplied realized HRU .met and matching year:
- compare RAD, Tmin, Tmax, HUM and WIND to all 33 supplied district series;
- use multiple dates;
- require a unique district match within renderer rounding;
- WET, RAIN and ETref are excluded from district identification.

Result artifact:
  hru, inferred_district, matched_days, max_abs_error, ambiguity_count.

## RAIN/WET invariant gate

For every realized row:
- if RAIN < historical output precision threshold for zero, require WET == 0;
- if RAIN > 0, require WET > 0.

Classify each row after district identification:
- DISTRICT: output WET equals local district WET within rounding;
- FORCED_DRY_ZERO: RAIN output zero and WET output zero;
- IMPUTED_HISTORICAL_MAX: RAIN positive, local district WET < 0.01, output equals max(0.01, daily maximum WET among districts);
- UNEXPLAINED: none of the above.

No modernized policy is admitted while UNEXPLAINED rows remain.

## Grid aggregation gate

When a realized period with supplied precipitation/evaporation rasters is available:
- build sparse donor-equal HRU-pixel weights;
- aggregate RAIN and ETref;
- reproduce realized output to renderer precision;
- compare source-current membership as a falsification control.

The district and grid gates are independent.
