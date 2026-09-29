# P12 correction policy

Historical Fortran behavior is evidence, not scientific truth.

## Two-track rule

Every reconstructed producer has two explicit modes of reasoning:

1. HISTORICAL_COMPAT
   - reproduce hrulist2SWAP behavior exactly enough to establish provenance and regression;
   - retain historical quirks and suspected defects as named fixtures.

2. CORRECTED
   - may change historical behavior only after the old behavior is isolated by a failing/diagnostic test;
   - correction must have an explicit physical, dimensional, numerical or data-contract rationale;
   - quantify national and per-HRU impact;
   - retain before/after outputs and decision record.

A corrected implementation must never silently redefine the historical baseline.

## Defect classes to audit

- unit conversions and sign conventions;
- left/right or positive/negative flux decomposition;
- time aggregation and leap-year/calendar handling;
- weighted versus unweighted HRU aggregation;
- fallback when nusvatwb == 0;
- majority/tie behavior;
- use of representative versus all member SVATs;
- missing/NoData propagation;
- hard-coded constants and dates;
- file/path logic leaking into scientific values;
- off-by-one array/time indexing;
- boundary-condition semantics;
- crop/root-depth precedence;
- drainage aggregation;
- meteorological district assignment;
- area weighting and fractional-cell handling.

## Admission

A historical mismatch is not automatically a bug.
A Fortran match is not automatically correct.

Corrections are admitted only with:
- preregistered defect hypothesis;
- minimal reproducer;
- historical baseline result;
- corrected result;
- physical/dimensional justification;
- impact assessment;
- regression protecting the corrected behavior.
