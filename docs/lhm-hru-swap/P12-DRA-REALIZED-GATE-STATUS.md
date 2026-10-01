# P12 DRA realized reproduction gate status

Status:
**PARTIALLY QUALIFIED; STATIC04/NATURE SOURCE-SIDE CLOSED; SWALLO PROVENANCE SPLIT EXPLICIT; 49-RUN REALIZED GATE BLOCKED**

## Source-side reconstruction already available

Available/reconstructed:
- five drainage-system conductance families;
- primary/secondary/tertiary infiltration-factor families;
- drainage bottom/level families;
- HRU membership semantics;
- all-member aggregation authority;
- DRARES / INFRES formulas;
- conductance-weighted depth/level formulas;
- system-4 nature shutdown rule;
- dqsat-to-L rule.

Core formulas are implemented in:
- `tools/p12_dra_aggregate.py`;
- `tools/generate_dra.py`.

## Regression tooling now complete

Single-file semantic parser:
- `tools/dra_semantic_oracle.py`.

Multi-run semantic regression harness:
- `tools/regress_dra_cases.py`;
- `tests/test_regress_dra_cases.py`.

The multi-run harness:
- discovers realized and candidate DRA files by run id;
- requires one-to-one run coverage;
- compares global and per-system DRA semantics;
- separates exact matches, preregistered expected differences and unexplained differences;
- fails admission when candidate runs are missing/extra;
- requires every preregistered expected difference to actually occur.

Therefore the 49-run gate no longer has an implementation/harness blocker. STATIC04 source-side candidate generation is now also qualified; once the realized 49-run oracle bytes become available, the complete comparison can run in one command.

## Raw Project files

The two previously missing rasters are located in Project Files:
- `ahn_f250_m.asc` — 23,402,759 bytes;
- `grensvlak_NHIWQ_v2_fill.asc` — 3,521,406 bytes.

Direct raw-byte materialization remains unauthorized in the current runtime. However, both raster contents have now been recovered completely through text line-range materialization and passed a full 1200 x 1300 shape gate. Numerical-content recovery and semantic hashes are recorded in `P12-DRA-R3-RASTER-RECOVERY-2026-09-30.md`.

Therefore the source-raster content blocker is resolved for scientific/numerical reconstruction. Raw-byte identity remains unverified and must not be conflated with numerical-content equivalence.

The earlier 49-run realized DRA set is described in repository authority and remains present as `run_files.zip`, but its raw bytes are not authorized for materialization in the current runtime. A full Library crawl found only this single archive object, so there is currently no alternative duplicate to use.

Only one loose raw DRA oracle is currently recoverable:
- `2000.dra`;
- SHA-256 `85dff23754d138b12e3084e5c06c6ad3eb77880c64d7a24f85aa48aae4acd15e`.

## Independent run-2000 DRA oracle

Observed realized values:

| system | DRARES d | INFRES d | L cm | ZBOTDR cm | SWALLO |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 100000 | 100000 | 100 | 0.00 | 3 |
| 2 | 824 | 2498 | 80 | -97.79 | 1 |
| 3 | 212 | 725 | 80 | -100.00 | 3 |
| 4 | 17040 | 100000 | 80 | -50.06 | 3 |
| 5 | 30 | 100000 | 80 | -24.17 | 3 |

This independently supports:
- systems 4 and 5 use `INFRES = 100000` in the realized file;
- active systems 2-5 use `L = 80 cm`.

Recovered historical Runs row for run 2000:
- `dqsat = 20`.

Hence:
`L / 4 = 20 = Runs.dqsat`
for systems 2-5.

This proves historical dqsat propagation into DRA geometry.

STATIC04 source-side reconstruction has since established that run 2000 is itself non-discriminating:
- legacy reconstructed dqsat = 20;
- representative-SVAT dqsat = 20;
- historical Runs.dqsat = 20;
- realized active-system L/4 = 20.

Across the full 10,242-HRU source population, however, legacy and representative-SVAT dqsat differ for 2,771 HRUs. See `P12-STATIC04-DQSAT-RESULT-2026-09-30.md`.

## Nature discrimination

Run 2000 has final representative `lu_id = 1`, therefore schema-first `isnatuur = false`.

Its realized system 4 has:
- DRARES4 = 17040, below the independent >20000 shutdown criterion;
- nonzero drainage depth;
- system 4 remains active.

This is consistent with representative-landuse semantics, but non-discriminating because the legacy pre-override nature classification is not independently available for run 2000.

## What is qualified

Qualified:
- DRA serialization shape;
- system ordering;
- all-member support rule;
- DRARES/INFRES algebra in unit tests;
- multi-run regression harness;
- run-2000 dqsat propagation from Runs to realized L;
- run-2000 system-4 state consistency with representative non-nature land use.

Not yet qualified across the realized 49-run oracle:
- exact DRARES/INFRES numeric reproduction;
- ZBOTDR/LEVEL reproduction;
- realized classification of STATIC04 discriminating cases;
- full 49-run SWALLO classification under the explicit supplied-source versus realized-production provenance modes.

Nature/DRA4 authority itself is now source-side closed. Across all 10,242 HRUs, legacy pre-override land use and representative-SVAT land use differ for 1,974 HRUs, but the exact supplied-source nature predicate is identical for all 10,242. Therefore no realized 49-run DRA4 difference may be attributed to legacy-versus-schema nature ordering in the current population. See `P12-NATURE-DRA4-AUTHORITY-RESULT-2026-09-30.md`.

## Admission blocker

Current blocker classification:

**BLOCKER_RAW_49RUN_DRA_REALIZED_ORACLE**

The source-side STATIC04 authority question is no longer blocked:
- authoritative `svat_repr` recovered for 10,242 HRUs;
- exact representative source-cell mapping recovered through the persisted member relation x/y;
- representative-SVAT dqsat reconstructed;
- exact legacy majority-BFE dqsat reconstructed;
- 2,771 source-side discriminating HRUs identified.

The remaining admission evidence is the raw 49-run realized oracle set. Required next steps when access clears:
1. extract all 49 realized DRA files from `run_files.zip`;
2. intersect those HRUs with the STATIC04 comparison table;
3. classify active-system `L/4` as legacy, schema-first, non-discriminating or unexplained;
4. run full `regress_dra_cases.py` for DRARES/INFRES/ZBOTDR/LEVEL/SWALLO semantics;
5. treat nature/DRA4 as zero-expected-difference for the current population and reject it as an explanation for any realized mismatch;
6. require zero unexplained differences before direct DRA admission.

Do not infer representative dqsat from realized DRA outputs. Realized `L/4` remains an independent oracle only.

## SWALLO provenance mismatch — run 2000

The independent run-2000 oracle now discriminates the forced-system SWALLO rule.

Recovered source-side river-infiltration indicator:
- equal-member mean of the independent `riv_infil` field;
- available in `SVAT_INFO_HRU.CSV` under the historically misleading header `wegzijgingz(mm/j)`;
- run 2000 value: 11.8204166667.

Realized run 2000:
- `INFRES3 = 725`;
- `SWALLO3 = 3`.

The active supplied v0.38 source rule `system > 3 OR INFRES > 20000 OR infil_avg < 10` predicts SWALLO3=1 and is therefore falsified for the realized executable.

The source-history v0.27 statement `SWALLO=3 voor sys>2` predicts SWALLO3=3 and matches the realized oracle.

Modern code now exposes two explicit provenance modes:
- `SUPPLIED_SOURCE_V038`;
- `REALIZED_PRODUCTION_COMPAT`.

See:
- `P12-SWALLO-REALIZED-PROVENANCE-2026-09-30.md`;
- `P12-SWALLO-RIVER-INFILTRATION.md`;
- `tools/p12_swallo.py`.

The DRA serializer accepts an explicit SWALLO provenance mode. The default remains supplied-source behavior; realized-production compatibility must be selected explicitly.

This mismatch is now an expected provenance difference, not an unexplained renderer difference.


## Targeted STATIC04 discriminator

The 49-run validation set explicitly contains HRU 7877.

Independent source-side reconstruction:
- legacy majority-BFE dqsat = 18 cm;
- representative-SVAT dqsat = 17 cm.

Therefore, for any active positive-length drainage system in realized `7877.dra`:
- `L = 72` cm supports the legacy authority;
- `L = 68` cm supports representative-SVAT authority;
- another active-system L is unexplained.

This narrows the minimum evidence needed to classify STATIC04 executable behavior. A loose raw `7877.dra` would be sufficient for that authority question even before the complete 49-run archive is available. Full direct-DRA admission still requires the complete multi-run gate.

See:
`P12-STATIC04-TARGETED-REALIZED-DISCRIMINATOR-7877.md`.


## 1 October 2026 update — raw 49-run blocker removed

The former `BLOCKER_RAW_49RUN_DRA_REALIZED_ORACLE` is no longer active.

Recovered user-supplied archive:
- `run_files(1).zip`;
- SHA-256 `46f1fc6b6f4aa01265db950c8ca78f9c4714a97d11cfa4d8f0c66b4dea7a05e3`;
- 49 realized run directories;
- each contains `swap.swp`, run-specific DRA, BBC and MET inputs.

### STATIC04 realized closure

Full 49-run classification:
- NON_DISCRIMINATING: 34;
- EXPLAINED_LEGACY: 15;
- EXPLAINED_SCHEMA_FIRST: 0;
- UNEXPLAINED: 0.

All 15 discriminating cases follow the legacy majority-BFE dqsat used by the realized executable.

Modern production authority remains representative-SVAT dqsat. Therefore the schema-first DRA candidate must intentionally differ from realized history on 75 spacing paths:
15 runs x 5 `systems.N.L`.

Preregistered in:
`config/p12/dra-49run-static04-expected-differences-v1.yml`.

Authority:
`P12-49RUN-STATIC04-REALIZED-RESULT-2026-10-01.md`.

### SWALLO 49-run closure refinement

The recovered 49-run archive substantially changes the earlier run-2000-only interpretation.

Against 245 realized SWALLO scalars:
- active supplied v0.38 rule matches 241/245;
- 47/49 complete runs match;
- residuals are limited to HRUs 7868 and 7929;
- the run-2000/v0.27 universal system-3 forcing hypothesis has 25/245 mismatches.

The 49-run archive contains many system-3 rows with realized SWALLO3=1. Therefore a universal "realized production forces systems 3-5" rule is falsified.

Use:
- `SUPPLIED_SOURCE_V038` for the 49-run historical baseline;
- `RUN2000_V027_COMPAT` only for the separate run-2000/v0.27 provenance state.

The four v0.38 residual scalar mismatches are not qualified intentional differences and remain provenance/input-version questions.

Authority:
`P12-49RUN-SWALLO-REALIZED-RESULT-2026-10-01.md`.

### Revised remaining DRA gate

The remaining blocker is no longer missing realized evidence.

Remaining work before `DIRECT_DRA_PRODUCER_ADMITTED`:
1. generate the complete modern candidate DRA set from qualified source inputs;
2. run the 49-run semantic regression;
3. accept only the preregistered 75 STATIC04 L differences and separately qualified provenance differences;
4. investigate the two SWALLO residual runs rather than force-fitting them;
5. require zero unexplained DRARES/INFRES/ZBOTDR/LEVEL/SWALLO differences.

Current classification:
**REALIZED_ORACLE_RECOVERED_CANDIDATE_GENERATION_FULL_REGRESSION_PENDING**.
