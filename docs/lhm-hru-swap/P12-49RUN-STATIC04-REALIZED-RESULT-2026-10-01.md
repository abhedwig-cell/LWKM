# P12 49-run realized oracle recovery and STATIC04 classification — 1 October 2026

Status:
**RAW ORACLE RECOVERED; STATIC04 REALIZED GATE CLOSED**

## Recovered archive

User-supplied raw archive:
`run_files(1).zip`

SHA-256:
`46f1fc6b6f4aa01265db950c8ca78f9c4714a97d11cfa4d8f0c66b4dea7a05e3`

Archive structure:
- 324 ZIP entries;
- exactly 49 top-level realized run directories;
- HRU ids 7866..7945 with gaps;
- every run contains `swap.swp`, a run-specific `.dra`, `.bbc` and `.met`;
- crop/CO2 support files are present where required.

This removes the former raw-access blocker for the 49-run realized oracle.

## STATIC04 method

Source-side predictions were reconstructed independently from:
- `csv/export_HRUschema_10242.csv`;
- `csv/export_svat_HRU_NRU_10242.csv`;
- recovered numerical `grensvlak_NHIWQ_v2_fill.asc`.

The recovered dqsat raster was reassembled to:
- 1200 x 1300;
- exactly 1,560,000 values;
- semantic float64-array SHA-256
  `79fdfc37153aea04a9ec24cef1b3d981f519aaed062f8c07e8922766bb3849cd`.

This matches the previously qualified R4 semantic hash.

For every realized DRA file:
- all non-fallback `L1..L5` values imply the same `L/4`;
- no run has internally inconsistent realized dqsat propagation.

The realized `L/4` value was then compared against:
1. legacy majority-BFE dqsat;
2. representative-SVAT dqsat.

Realized output was never used to construct either prediction.

## Result over all 49 realized runs

| classification | runs |
| --- | ---: |
| NON_DISCRIMINATING | 34 |
| EXPLAINED_LEGACY | **15** |
| EXPLAINED_SCHEMA_FIRST | **0** |
| UNEXPLAINED | **0** |

The 15 source-side discriminating HRUs are:

`7871, 7877, 7909, 7910, 7911, 7920, 7922, 7923, 7927, 7928, 7929, 7930, 7935, 7937, 7942`.

Every one of those 15 realized runs uses the legacy majority-BFE dqsat.

Examples:
- 7871: legacy 7, representative 9, realized 7;
- 7877: legacy 18, representative 17, realized 18;
- 7910: legacy 20, representative 4, realized 20;
- 7928: legacy 7, representative 20, realized 7;
- 7935: legacy 20, representative 7, realized 20.

No discriminating case supports the representative-SVAT value as the behavior of the executable that generated this 49-run archive.

## Interpretation

This closes the previously open executable-history question.

The realized 49-run executable follows the legacy dqsat ordering in every available discriminating case.

That does **not** overturn the modern source-side authority decision.

The modern production rule remains:
- source dqsat at Piet's authoritative representative SVAT.

Therefore the modern DRA producer is expected to differ intentionally from the realized historical DRA spacing for these 15 runs.

For every one of the 15 discriminating runs, all five realized systems have non-fallback spacing. A schema-first candidate therefore changes `L1..L5` in each of those runs.

Expected STATIC04 DRA difference paths:
- 15 runs x 5 systems = **75 preregistered L differences**.

All other DRA fields still require ordinary regression identity unless another separately qualified intentional difference applies.

## Realized dqsat distribution in the 49-run archive

Inferred from active `L/4`:
- 7 cm: 9 runs;
- 9 cm: 4 runs;
- 10 cm: 19 runs;
- 13 cm: 1 run;
- 18 cm: 5 runs;
- 20 cm: 11 runs.

## Classification

Historical executable behavior:
**STATIC04_49RUN_REALIZED_EXECUTABLE_LEGACY_CONFIRMED**

Modern authority:
**STATIC04_REPRESENTATIVE_SVAT_CORRECTION_REMAINS_ADMITTED_SOURCE_SEMANTICS**

The difference is intentional and must remain visible.

## Remaining DRA admission work

Still required before `DIRECT_DRA_PRODUCER_ADMITTED`:
1. generate the complete schema-first candidate DRA set from qualified inputs;
2. compare DRARES/INFRES/ZBOTDR/LEVEL/SWALLO for all 49 runs;
3. preregister the 75 STATIC04 `L` differences;
4. apply the separately qualified SWALLO provenance policy;
5. require zero unexplained differences.

