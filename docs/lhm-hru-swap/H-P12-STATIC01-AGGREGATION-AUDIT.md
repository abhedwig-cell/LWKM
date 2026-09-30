# H-P12-STATIC01 — static aggregation audit candidates

## Irrigation threshold resolution

Project-owner clarification: 0.37 is an intentionally calibrated threshold. The source comment mentioning 30% is stale and must not be used to change behavior.

Historical calibrated implementation:
- converts each member irr_switch>0 to 1, else 0;
- computes unweighted source-member fraction av;
- forces irrigation on if av > 0.37;
- then takes majority irrigation source/type among irrigated members.

Status:
- threshold 0.37: CONFIRMED_CALIBRATED, preserve;
- comment 30%: DOCUMENTATION_DEFECT;
- support is currently member-count/full equal source cells. Do not silently change to uopp weighting. Reopen only if calibration provenance establishes that 0.37 was calibrated on active-area fraction.

## RDS fallback control-flow candidate

Apparent intended logic:
1. collect rds where bfe==bfe_maj AND lgn==lgn_maj;
2. if no such members exist, collect rds where lgn==lgn_maj;
3. take MAJORITYR4.

Actual loop:
  for each member:
    if bfe+lgn match: append rds
    if nutp==0 and lgn match: append rds

Because fallback is evaluated inside the loop, an early lgn-only member can be appended before a later bfe+lgn member is encountered. The resulting sample can mix fallback and preferred populations.

This is not equivalent to the apparent two-stage selection.

Required falsification:
- reconstruct all HRUs;
- compare current-loop result with true two-stage result;
- identify changed HRUs;
- compare realized SWP rooting parameter where available;
- inspect historical executable/source provenance.

Status: DEFECT_CANDIDATE_CONTROL_FLOW.

## DQSAT

dqsat_maj selects members with bfe==bfe_maj then MAJORITYR4. No fallback is actually implemented despite an empty IF block. Validate that every realized HRU has at least one bfe-majority member (expected by definition) and MAJORITYR4 semantics for real values.

## C1 mixed-boundary aggregation

Within bbc_maj:
  c1_avg = 1 / mean(1/c1)
and bbc3weight proportional to 1/c1.

This is conductance-weighted/harmonic aggregation and mathematically coherent for parallel vertical resistances. It is separate from active prescribed-flux QBOT2.
