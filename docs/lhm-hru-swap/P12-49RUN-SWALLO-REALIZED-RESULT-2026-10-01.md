# P12 49-run SWALLO realized provenance result — 1 October 2026

Status:
**49-RUN ORACLE STRONGLY SUPPORTS V0.38-LIKE FORCED-SYSTEM RULE; TWO INPUT-PROVENANCE RESIDUALS REMAIN**

## Inputs

Recovered raw 49-run oracle:
`run_files(1).zip`
SHA-256:
`46f1fc6b6f4aa01265db950c8ca78f9c4714a97d11cfa4d8f0c66b4dea7a05e3`

Source-side river-infiltration reconstruction:
- exact HRU membership from `export_svat_HRU_NRU_10242.csv`;
- per-SVAT indicator from `SVAT_INFO_HRU.CSV`, historical header `wegzijgingz(mm/j)`;
- equal-member mean, matching supplied source.

Compared rules:

### Active supplied v0.38

`system > 3 OR INFRES > 20000 OR indicator < 10 -> SWALLO=3`

### Run-2000 / v0.27 compatibility hypothesis

`system > 2 OR INFRES > 20000 OR indicator < 10 -> SWALLO=3`

## Result

Across 49 runs x 5 systems = 245 realized scalar SWALLO values:

### v0.38 rule
- matches: **241 / 245**;
- mismatches: **4 / 245**;
- complete run-level match: **47 / 49**.

Residual mismatches are confined to:
- HRU 7868, systems 1 and 2;
- HRU 7929, systems 2 and 3.

Using the recovered current source-side indicator:
- HRU 7868 mean indicator = 8.6042;
- HRU 7929 mean indicator = 9.96479.

The v0.38 threshold therefore predicts SWALLO=3 for those rows, while the realized archive contains SWALLO=1.

Do not force-fit these four residuals. Possible causes include source-raster/version provenance differences or executable/input-version mismatch.

### run-2000 / v0.27 forced-system rule
- mismatches: **25 / 245**;
- complete run-level match: **26 / 49**.

Most importantly, 22 system-3 rows in the 49-run archive are realized as SWALLO3=1. Those rows directly falsify a universal "systems 3-5 are always forced" rule for this archive.

## Strong discriminator against the old REALIZED_PRODUCTION_COMPAT name

Examples where:
- system = 3;
- INFRES <= 20000;
- reconstructed indicator >= 10;
- realized SWALLO3 = 1:

7874, 7876, 7877, 7910, 7912, 7915, 7916, 7917, 7920, 7923,
7924, 7927, 7928, 7930, 7931, 7932, 7933, 7934, 7936, 7937, 7938
plus one additional system-3-compatible case outside the forced-rule mismatch set as classified by the full table.

Therefore the earlier label `REALIZED_PRODUCTION_COMPAT` is too broad.

Run 2000 and the 49-run archive represent different realized provenance states for SWALLO.

## Revised interpretation

The evidence now supports three distinct concepts:

1. `SUPPLIED_SOURCE_V038`
   - active source rule;
   - strongly consistent with the 49-run archive;
   - 241/245 scalar matches, with four unresolved source/input provenance residuals.

2. `RUN2000_V027_COMPAT`
   - systems 3-5 forced;
   - matches the independent run-2000 discriminator and v0.27 source-history statement;
   - not a general production rule for the 49-run archive.

3. Modern production authority
   - should not be inferred from either historical executable state alone;
   - must retain the source-bound river-infiltration indicator and an explicit chosen compatibility/modern policy.

## Admission consequence

Do not preregister the four v0.38 residual mismatches as intentional differences yet.

They are not qualified defects.

For the 49-run DRA regression:
- v0.38 is the correct historical baseline candidate for SWALLO;
- HRUs 7868 and 7929 remain targeted provenance investigations;
- any other SWALLO difference is unexplained.

Classification:

**SWALLO_49RUN_V038_BASELINE_QUALIFIED_WITH_TWO_RUN_PROVENANCE_RESIDUAL**

and:

**UNIVERSAL_REALIZED_PRODUCTION_SYS3_FORCE_FALSIFIED**.
