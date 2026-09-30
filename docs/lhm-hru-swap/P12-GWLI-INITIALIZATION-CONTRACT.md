# P12 GWLI initialization contract

## Meaning

GWLI is the initial groundwater level used to initialize the SWAP calculation.

Legacy source reads:
  head_<TimStart>_l1.idf
from the MODFLOW head directory into hh per source cell.

For each HRU:
  hh_avg = equal-member mean(hh)
  glk_avg = equal-member mean(ground elevation)
  GWLI = min(0, round((hh_avg - glk_avg) * 100))

Unit:
  cm relative to ground surface; non-positive by construction.

## Project-owner clarification

GWLI is not a highly sensitive representative HRU parameter. It should be approximately physically correct as a starting condition. It is understood to originate from the MODFLOW stationary/initial groundwater head used at the simulation start.

Therefore modernization priority is:
- preserve a plausible MODFLOW-derived initial groundwater depth;
- avoid unnecessary complexity or calibration;
- do not confuse GWLI with Piet's representative HRU identity;
- let SWAP spin toward its dynamic state during simulation.

## Modern semantics

Preferred:
  derive GWLI from the MODFLOW initial/stationary head field at simulation start and local ground elevation, with explicit source provenance.

Historical compatibility:
  retain equal-source-cell mean formula unless a simpler representative-cell initialization is shown to be equally robust.

Validation:
- finite head and ground elevation;
- GWLI <= 0;
- flag implausibly deep values;
- exact historical reproduction is useful but not an admission-critical scientific requirement if the new initialization is physically equivalent.

Status: SEMANTICS_RESOLVED_INITIALIZATION_LOW_SENSITIVITY.
