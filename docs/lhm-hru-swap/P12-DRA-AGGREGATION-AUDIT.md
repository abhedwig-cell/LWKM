# P12 DRA aggregation audit hypotheses

Project-owner clarification: using ALL HRU member cells for drainage aggregation is intentional. Do not treat all-member aggregation as a defect.

Audit therefore targets the mathematics inside that design.

## H-DRA-COND01 parallel conductance aggregation

Current:
  cdr_sum = sum(cdr_i)
  drnres = 62500 * N / cdr_sum

If cdr_i is a cell-total conductance [m2/day] for a 62,500 m2 source MODFLOW cell, this yields:
  drnres = total full-cell area / total conductance [day]
which is physically consistent for parallel drainage over N equal MODFLOW cells.

If cdr_i is instead normalized to uopp/active area, the 62,500*N numerator may be wrong. Bind native CDR units/support from source generation before changing.

## H-DRA-INF01 infiltration resistance

Current:
  inf_sum = sum(cdr_i * inf_i)
  infres = 62500 * N / inf_sum

This is consistent only if inf_i is a dimensionless infiltration conductance factor multiplying drainage conductance. Verify source semantics and range.

## H-DRA-DEP01 drainage depth weighting

Current:
  dep = sum(cdr_i * (glk_i - bodh_i)) / sum(cdr_i)

This is a conductance-weighted depth. For parallel drains this is physically defensible because it preserves the linear drainage relation at a common HRU groundwater head, subject to differing ground levels.

Check exact equivalence:
  sum[c_i (h - z_i)] == C_total (h_rep - z_rep)
for the chosen representative ground/head datum.

## H-DRA-LEVEL01 summer/winter level transform

Current pre-transform:
  peil_abs_rep = glk_avg - sum[c_i*(glk_i-peil_i)]/sum[c_i]
Then output depth:
  max/min repairs; LEVEL = -depth*100.

This mixes an UNWEIGHTED glk_avg with a CONDUCTANCE-WEIGHTED relative water-level depth. If glk varies within an HRU, that may not preserve the conductance-weighted absolute level.

Candidate mathematically consistent alternatives:
A. weighted relative depth:
  depth_rep = sum[c_i*(glk_i-peil_i)]/sum[c_i]
B. weighted absolute level:
  peil_rep = sum[c_i*peil_i]/sum[c_i]
with an explicitly chosen representative ground datum for conversion to SWAP depth.

The current algebra is not automatically equivalent to either when glk_avg != sum(c_i glk_i)/sum(c_i).

This is a priority audit candidate.

## H-DRA-AREA01 full-cell versus active-area support

Because all-member is intentional, distinguish:
- full MODFLOW cell area: 62,500*N;
- MetaSWAP active area: sum(uopp_i).

Do not replace the numerator by sum(uopp) unless native drainage conductance is shown to be supported on active area. The current full-cell formula may be exactly right for MODFLOW drainage conductance.

## Validation

For 49 realized DRA files:
1. reproduce current all-member formulas;
2. compare each DRARES/INFRES/ZBOTDR/LEVEL;
3. only then test algebraically equivalent/corrected candidates;
4. quantify changes separately from historical reproduction.
