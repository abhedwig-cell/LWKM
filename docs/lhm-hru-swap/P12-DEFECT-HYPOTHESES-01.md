# P12 Fortran defect hypotheses 01

No production behavior is changed by this document.

## H-P12-DRA-WB01: drainage aggregation ignores intended water-balance subset

Evidence in hrulist2SWAP.f90:
- comment states average drainage characteristics are determined using cells participating in wb;
- code assigns nutp = nusvatwb and immediately overwrites it with nutp = nusvat;
- inner IF (issvatwb(jj)) guards are commented out.

Hypothesis: drainage parameters are currently aggregated over all HRU member SVATs although the intended/previous design was the water-balance subset.

Test required:
- identify HRUs where nusvatwb < nusvat;
- compute historical all-member DRA parameters;
- compute WB-subset candidate parameters;
- quantify differences and check physical consistency.

Do not correct until this is run.

## H-P12-BBC-WEIGHT01: bottom flux aggregation may use cell-count instead of area weighting

Historical code over issvatwb members computes:
  qq += (head2-head1)/c1
  qq_cm = 100 * qq / nusvatwb

The member areas are available and demonstrably not universally equal in the realized SVAT data.

Hypothesis: if conductance/head flux represents a per-area or cell-total quantity whose aggregation should respect actual SVAT area, dividing by member count can bias HRU bottom flux when member areas differ.

Alternative hypothesis: c1 and source grids are already normalized such that equal-member averaging is intentional.

Required before correction:
- establish units of head grids and c1;
- derive dimensions of each term;
- compare count-weighted and area-weighted HRU flux on heterogeneous-area HRUs;
- check aggregate mass balance against source LHM/MODFLOW flux.

## Additional audit observation

Several HRU scalar properties (xc, yc, hh, glk, infiltration) use unweighted AVERAGE over member SVATs. This is not automatically wrong. Each property needs a semantic weighting decision rather than a blanket area-weighting rewrite.
