# P12 water-balance selection anomaly

Preregistered from active hrulist2SWAP source. No correction yet.

## Observed chain

During HRU2svat reading:
- each member SVAT starts isverdacht = FALSE;
- if svat_id != svatdonor, isverdacht = TRUE;
- log labels these as "verdachte cellen".

Later:
  HRUlist%issvatwb = svatlist%isverdacht

Thus the time-dependent bottom-boundary and meteo aggregation selection uses the members flagged as "verdacht".

If an HRU has zero such members:
- nusvatwb is replaced by nusvat;
- all issvatwb are set TRUE;
- HRU is marked isproblem=TRUE.

## Why this is suspicious

The semantic names suggest "verdacht" and "participates in water balance" are different concepts. Yet they are directly equated.

Possible explanations:
1. intentional: non-donor/modified cells are exactly the subset whose hydrological forcing should define the HRU;
2. inverted naming: isverdacht actually means usable/selected in this file generation context;
3. defect introduced during the 2026 suspicious-cell revisions;
4. HRU2svat donor semantics make the apparent inversion correct.

Do not change until HRU2svat/svatdonor construction is reconstructed.

## Impact if wrong

issvatwb controls at least:
- active qq/QBOT2 aggregation;
- precipitation and evaporation aggregation;
- areawb_sum;
- historical FLF/QLAT diagnostics.

Therefore this is a higher-priority scientific audit than FLF normalization for current production.
