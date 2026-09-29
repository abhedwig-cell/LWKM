# P12 WET / rainfall-duration contract

Project-owner domain clarification:

WET is rainfall duration.

Hard consistency invariants:
- precipitation == 0 => WET must be 0;
- precipitation > 0 => WET must be > 0.

Therefore the historical P12 repair logic has a valid purpose: enforce a physically/data-consistent precipitation-duration pair.

## Historical implementation

If aggregated HRU rain < 0.01:
  rain = 0
  WET = 0

Else, if selected district WET < 0.01:
  WET = max(0.01, max WET across all districts for that day)

Interpretation:
- 0.01 is both the precipitation zero threshold and minimum positive WET threshold in this implementation;
- the cross-district maximum is an imputation policy for inconsistent/missing positive-rain duration, not the physical invariant itself.

## Audit separation

CONFIRMED contract:
  dry -> zero duration
  wet -> positive duration

OPEN policy question:
  for wet + missing/zero local WET, should imputation be:
  - historical national daily maximum;
  - nearest/related district;
  - climatological/local estimate;
  - derived from subdaily precipitation if available;
  - fail/flag instead of impute?

Modern code must expose this as a named policy and provenance flag, not hide it inside the writer.

Recommended output provenance:
  wet_source = DISTRICT | FORCED_DRY_ZERO | IMPUTED
  wet_imputation_policy = historical_national_max | ...

Historical compatibility retains national-max exactly.
