# P12 WBSEL01 impact run protocol

Input authority:
  export_svat_HRU_NRU_10242.csv

Phase A — structural, mandatory:
- parse all memberships;
- group by HRU;
- reproduce historical selection;
- apply corrected donor-equal selection;
- assert every HRU has >=1 corrected donor;
- report changed selections and historical fallbacks;
- report provenance counts.

Phase B — static hydrological spot checks:
- join c1 and representative head snapshots;
- compute historical/corrected QBOT2;
- select HRUs spanning no change, small donor-target fraction, large fraction, Restgroep.

Phase C — time-series:
- stream head periods; no need to materialize full HRU x time matrix;
- calculate delta QBOT2 per period and summary statistics;
- separately stream precipitation/evaporation and calculate area-weighted deltas.

Acceptance:
- historical mode matches Fortran sample output before corrected mode is evaluated;
- corrected mode has no zero-donor HRUs;
- large deltas receive source-level inspection;
- correction is admitted separately from renderer modernization.
