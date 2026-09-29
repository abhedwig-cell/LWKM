# H-P12-WBSEL01 — donor-selection inversion confirmed semantically

Status: DEFECT_CONFIRMED_SEMANTIC; numerical impact quantification remains.

## Upstream clustering semantics

The documented HRU clustering algorithm distinguishes:
- successful clustered SVATs / donor population;
- remainder targets that are assigned to a donor HRU by weighted nearest-neighbour matching;
- final unassignable remainder that receives new HRUs.

The final export deliberately stores both each row's original (_orig) attributes and its assigned/representative (_donor) attributes.

Thus svat_orig != svat_donor means a target SVAT has been represented by another donor; it does not mean that the target is the preferred water-balance representative.

## Realized 10242 export

export_svat_HRU_NRU_10242.csv:
- 427,656 data rows;
- labels found by indexed exact counts:
  - valid | HRU group size OK | NRU group size OK: 369,752
  - Toegevoegd: 57,791
  - Restgroep: 113
- inspected Toegevoegd rows have svat_orig != svat_donor;
- inspected valid rows have svat_orig == svat_donor.

## Consumer defect

hrulist2SWAP sets:
  isverdacht = (svat_orig != svat_donor)
  issvatwb = isverdacht

and uses issvatwb for current QBOT2 qq plus precipitation/evaporation aggregation.

This selects donor-matched targets rather than the upstream donor/original HRU-derivation population, except for fallback-to-all when no non-donor exists.

Given the upstream documented semantics, this is now classified as a semantic inversion defect, not merely a naming anomaly.

## Correction candidate

Do not patch production yet. Candidate:
  issvatwb = (svat_orig == svat_donor)

Before admission:
- compute per-HRU population impact;
- compare historical/corrected QBOT2, precipitation and evaporation on representative HRUs;
- check intended handling of the 113 Restgroep records;
- preserve historical behavior fixture.
