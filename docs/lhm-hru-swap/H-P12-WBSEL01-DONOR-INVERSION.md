# H-P12-WBSEL01 — probable donor-selection inversion

Status: DEFECT_CANDIDATE_STRONG. No production correction yet.

## Independent producer evidence

LWKM_makeHRU.f90 documents that the SVATs used for HRU derivation are those for which:
  svat_orig == svat_donor

Its discharge diagnostic explicitly selects exactly that subset:
  IF (svat == svatdonor) THEN
      selected discharge/runoff += ...
  ENDIF

Thus equality with donor is positively identified upstream as the selected/original HRU-derivation subset.

## Consumer behavior

hrulist2SWAP.f90 instead does:
  isverdacht = FALSE
  if svat != svatdonor: isverdacht = TRUE
  issvatwb = isverdacht

Therefore its water-balance subset is the complement of the upstream selected donor subset, except that if the complement is empty it falls back to all members.

## Hypothesis

The assignment to issvatwb is inverted. Intended likely semantics:
  issvatwb = (svat == svatdonor)
or an equivalent explicit selection flag.

This may have been introduced/reworked during v0.35/v0.36 suspicious-cell changes in March 2026, but version history alone does not prove introduction date.

## Required falsification

Using realized HRU2SVAT:
1. classify each membership as donor-equal or donor-different;
2. count HRUs/members in both groups;
3. reproduce historical issvatwb exactly;
4. candidate corrected selection = donor-equal;
5. compare:
   - QBOT2 qq time series;
   - precipitation;
   - evaporation;
   - areawb_sum;
6. identify HRUs where historical fallback-to-all masks the inversion;
7. quantify national/HRU impact.

Also verify semantics against any pre-v0.35 HRUlist2SWAP/HRUlist2MetaSWAP source if recoverable.

No correction is admitted merely from naming; upstream explicit selection semantics plus numerical impact are required.
