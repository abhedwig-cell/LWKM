# WBSEL01 reconciliation against realized executable output

## New evidence

Supplied paired layer-1/layer-2 heads for Jan-Feb 1971 permit direct comparison with the first realized BBC row (labelled 31-dec-1970 but source logic overrides datum8(1)=TimStart, so the first computation uses TimStart=19710101 heads).

Across the 49 supplied realized runs:

Comparison to BBC column 1 on the first row:
- source-current historical selection (svat_orig != svat_donor, fallback all):
  MAE ≈ 0.050635 cm/day
  RMSE ≈ 0.085734 cm/day
  9/49 within ~0.00055 cm/day
- donor-equal selection (svat_orig == svat_donor):
  MAE ≈ 0.005062 cm/day
  RMSE ≈ 0.014399 cm/day
  26/49 within ~0.00055 cm/day

Controls with donor-only membership reproduce closely under both because historical fallback selects all.

Examples first row:
- HRU 7866 realized 0.2378; source-current 0.388834; donor-equal 0.237794.
- HRU 7913 realized 0.1382; source-current 0.174852; donor-equal 0.138154.
- HRU 7916 realized 0.1246; source-current 0.221175; donor-equal 0.124577.

## Revised classification

The donor-selection inversion is CONFIRMED_IN_SUPPLIED_SOURCE.

It is NOT currently established as a defect in the executable that generated the supplied realized runs. On the contrary, realized BBC output strongly indicates that executable used donor-equal or an equivalent selection.

The prior classification DEFECT_CONFIRMED_SEMANTIC must therefore be scoped to the supplied source state, not generalized to historical/production output.

## Residual mismatch

Donor-equal does not reproduce all 49 files exactly. Possible causes include:
- different vc/c1 raster version used for the realized run;
- different head snapshot/version;
- additional selection logic in the generating executable;
- executable/source provenance mismatch already demonstrated by the realized three-column BBC write.

Do not force-fit these residuals. Reconstruct executable provenance or compare more dates first.

## Governance consequence

Modern P12 should implement donor-equal semantics because it matches clustering authority and realized outputs far better, while retaining a source-current compatibility fixture separately.


## Six-snapshot confirmation

Using head pairs at 1971-01-01, 01-11, 01-21, 02-01, 02-11 and 02-21, matched to realized BBC labels 31-dec, 10-jan, 20-jan, 31-jan, 10-feb and 20-feb according to the source's paaltjes/TimStart handling, yields 294 HRU-date comparisons.

Overall:
- supplied-source selection MAE: 0.053486 cm/day; RMSE 0.089419; 31/294 within 0.00055 cm/day.
- donor-equal selection MAE: 0.005841 cm/day; RMSE 0.013584; 86/294 within 0.00055 cm/day.

Donor-equal has lower MAE on every one of the six snapshots. This strengthens the conclusion that the realized executable did not use the supplied-source inverted membership rule.
