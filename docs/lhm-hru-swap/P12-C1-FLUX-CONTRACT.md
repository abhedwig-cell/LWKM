# C1 / conductance-derived bottom flux resolution

Domain information: c1 is a hydraulic resistance in days.

Therefore, with head difference dh in metres:

  q_i = dh_i / c1_i

has unit m/day and is an intensive flux. The historical factor 100 converts m/day to cm/day for SWAP.

This resolves the dimensional question around qq. No additional division by geometric area is needed to obtain a flux unit.

The remaining aggregation question is support/weighting only.

Historical P12:
  q_HRU = mean(q_i) over issvatwb members.

This is correct if either:
1. each selected member represents an equal accounting area, or
2. q_i has already been mapped to a common parent-cell support for which equal-member averaging is intended.

If q_i is instead a local SVAT flux intensity with unequal representation areas A_i, the conservative HRU mean is:
  q_HRU = sum(q_i A_i) / sum(A_i).

Do not decide between these formulas from geometric SVAT area alone. Establish the representation-area semantics of c1/head pairs and the HRU water-balance selection first.

Updated status of H-P12-BBC-WEIGHT01:
- unit defect hypothesis: largely falsified; dh/c1 has correct flux dimensions.
- support-weighting hypothesis: remains open.
