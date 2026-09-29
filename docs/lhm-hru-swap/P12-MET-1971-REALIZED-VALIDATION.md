# P12 MET realized validation result — 1971

Validation population:
- 49 supplied realized HRU .met files;
- 365 days in 1971 each;
- 17,885 HRU-day rows;
- supplied NHI_regio.asc 250 m district grid;
- supplied 1971 district SWAP meteorology series.

## District selection

For every one of the 49 HRUs:
1. sample NHI_regio.asc at all HRU member coordinates;
2. take member-count MAJORITY, matching supplied source semantics;
3. compare realized RAD/Tmin/Tmax/HUM/WIND against that district's 1971 series.

Result:
- 49/49 district assignments reproduce the realized non-grid meteorology;
- maximum absolute difference across these fields is ~5e-5, consistent with output formatting;
- no district mismatch.

Districts represented in this 49-HRU sample:
- district 3: 19 HRUs
- district 12: 15
- district 4: 8
- district 9: 6
- district 6: 1

Status: METEO_MAJORITY_CONFIRMED_REALIZED.

## WET policy

All 17,885 realized HRU-days are explained by the historical rainfall-duration contract:

- FORCED_DRY_ZERO: 7,757 rows
- DISTRICT: 6,881 rows
- IMPUTED_HISTORICAL_MAX: 3,247 rows
- UNEXPLAINED: 0

Thus imputation is not a rare edge case in this validation population: it occurs in ~18.15% of HRU-days.

The historical policy is exactly reproducible:
- dry output rain -> WET 0;
- positive rain + positive local district WET -> local WET;
- positive rain + local WET <0.01 -> max(0.01, daily maximum WET across districts).

## Interpretation

The WET consistency mechanism is production-significant and must be preserved in historical compatibility.

Whether national-daily-maximum is the preferred future imputation is a separate scientific/design question. Do not change it incidentally during renderer modernization.

## Remaining MET gate

RAIN and ETref spatial aggregation still require same-period daily grid inputs for 1971, or realized .met for 2018, to independently reproduce the area-weighted grid side. The supplied 2018 grids cannot be directly compared to the supplied 1971 realized runs.
