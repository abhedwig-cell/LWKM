# H-P12-WBSEL01 population and QBOT2 impact

Inputs:
- export_svat_HRU_NRU_10242.csv
- vcw_L1.IDF supplied by project owner; c1 resistance [days]
- modflow.zip head_19700101000000_l1.IDF / l2.IDF

## Full population

427,656 memberships across exactly 10,242 HRUs.

By donor relation:
- svat_orig == svat_donor: 369,776 memberships
- svat_orig != svat_donor: 57,880 memberships

Every HRU has at least one donor-equal member.

Historical hrulist2SWAP membership:
- 7,229 HRUs contain non-donor members and therefore select the non-donor complement;
- 3,013 HRUs contain no non-donor member and trigger fallback-to-all;
- total historical selected memberships: 155,727.

Corrected donor membership:
- total selected memberships: 369,776;
- zero HRUs without a donor: 0.

Thus 7,229 / 10,242 HRUs have a structurally different membership selection.

Restgroep:
- 113 memberships in 24 HRUs;
- 24 donor-equal;
- 89 donor-different.
The equality rule naturally selects one donor source per these realized remainder HRUs.

## Native IDF resolution

vcw_L1.IDF:
- ncol 1200
- nrow 1300
- extent x 0..300000 m, y 300000..625000 m
- dx=dy=250 m
- float32 grid following a 52-byte header in this realized file.

The supplied head IDFs have 1124 x 1300 cells, x 0..281000 m, same y extent and 250 m resolution.

All 427,656 realized memberships mapped to valid c1/head cells in the supplied snapshot.

## QBOT2 snapshot impact

Using:
  q = 100 * (head_l2-head_l1)/c1 [cm/day]

and comparing historical versus donor-equal aggregation on 1970-01-01:

- 3,013 HRUs: identical, corresponding to historical fallback-to-all donor-only HRUs;
- 7,229 HRUs: numerically different;
- |delta| > 0.01 cm/day: 5,223 HRUs;
- |delta| > 0.1 cm/day: 1,341 HRUs;
- |delta| > 1 cm/day: 73 HRUs.

Delta corrected - historical [cm/day]:
- mean: -0.007599
- std: 0.203063
- median: 0
- 1st percentile: -0.509391
- 99th percentile: +0.448066
- min: -3.869308
- max: +5.804694

Largest absolute snapshot delta observed: 5.804694 cm/day (HRU 1778).

Interpretation:
This confirms material numerical impact of the semantic inversion. It does not by itself admit the correction. Next gate is historical-output reproduction on the exact production period/configuration and inspection of large-delta HRUs.
