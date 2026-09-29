# P12 FLF support closure experiment

Purpose: determine the physically appropriate normalization of MODFLOW FLF when used as a SWAP/HRU bottom flux. No candidate is assumed correct.

## Required source products

For the same selected period/time steps:
- raw bdgflf layer-1 MODFLOW budget grids used by hrulist2SWAP;
- uopp per source LHM cell;
- HRU-to-source-cell membership and issvatwb selection;
- historical HRU FLF written by hrulist2SWAP;
- qmodf and qlat products where available;
- time-step duration.

## Candidate representations per HRU

Let F_i be native FLF for selected source cell i.

A. HISTORICAL_ACTIVE_AREA
  depth_A = sum(F_i) / sum(uopp_i)

B. FULL_MODFLOW_AREA
  depth_M = sum(F_i) / (N * 62500)

C. CELL_DEPTH_MEAN
  convert each F_i to depth on 62500 m2, then equal-mean.
For equal cell areas B and C must be identical; this is an internal check.

Retain factor 100/time conversion separately until native F_i time units are confirmed.

## Closure tests

1. Native-volume reversibility
For each candidate, multiply derived depth by its stated denominator and recover sum(F_i). This checks implementation, not physics.

2. Existing qmodf/qlat identity
Reconstruct the historical relation qlat = qmodf - FLF on a common declared support. Determine which support conversion reproduces the existing derived grids without hidden area factors.

3. HRU aggregation conservation
Sum HRU reconstructed volumes and compare with direct sum of source-cell FLF over exactly the same selected source cells.

4. Sensitivity to uopp fraction
Stratify HRUs by mean uopp/62500. If A and B diverge strongly as active fraction falls, inspect whether historical SWAP bottom flux intentionally amplifies cell-total groundwater exchange onto the smaller active SWAP area.

5. Water-balance interpretation
Do not require the MetaSWAP surface balance to represent non-uopp cell area. Evaluate coupling exchange and full-cell balance separately.

## Decision classes

- HISTORICAL_CONFIRMED_PHYSICAL
- HISTORICAL_CONFIRMED_APPLICATION_SPECIFIC
- HISTORICAL_REPRODUCED_BUT_SUPPORT_UNRESOLVED
- DEFECT_CONFIRMED
- INSUFFICIENT_SOURCE_DATA

Any corrected implementation must retain the historical representation as a diagnostic output.
