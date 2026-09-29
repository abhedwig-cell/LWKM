# P12 DRA reconstruction status

Realized run_files.zip provides an independent .dra oracle for 49 HRUs.

Current supplied hrulist2SWAP source explicitly aggregates drainage over ALL HRU members despite a comment saying only water-balance members:
- nutp is assigned nusvatwb then overwritten by nusvat;
- issvatwb guards are commented out throughout length, conductance, infiltration-conductance, depth and water-level aggregation.

Observed formulas:
- leng_sum = sum(leng_i)
- dd_avg = dqsat_maj * 4 when length exists, else 100
- cdr_sum = sum(cdr_i)
- inf_sum = sum(cdr_i * inf_i)
- drnres_avg = clamp(62500 * n / cdr_sum, 1, 100000)
- infres_avg = clamp(62500 * n / inf_sum, 1, 100000)
- dep_avg = sum(cdr_i * (glk_i-bodh_i)) / sum(cdr_i)
- peil_sum/win are conductance-weighted before later depth conversion/clamping.

Systems with drnres > 20000, plus system 4 for nature, are disabled to 100000 resistance and zero levels/depth.

Realized DRA output format matches the current source shape: DRAMET=3, five systems, DRARES/INFRES/L/ZBOTDR/SWDTYP and seasonal DATOWL/LEVEL tables.

## Audit question

Unlike WBSEL01, do not assume drainage should use donor-equal members. Drainage aggregation may intentionally represent the complete HRU membership because assigned target cells contribute area/drainage infrastructure even though donor cells define representative hydrological forcing.

The source comment and commented issvatwb guards are evidence of an alternative intended design, not proof of a defect.

Next comparison must reconstruct BOTH:
A. all-member drainage (current source);
B. donor-source-only drainage;
and compare A to realized .dra first. If A reproduces realized output, all-member behavior is historical executable authority and any change to donor-only becomes a scientific redesign requiring separate justification.
