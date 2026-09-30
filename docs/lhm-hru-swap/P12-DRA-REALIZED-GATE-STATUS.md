# P12 DRA realized reproduction gate status

Status:
**PARTIALLY QUALIFIED, MULTI-RUN HARNESS READY, SOURCE RASTERS SEMANTICALLY RECOVERED**

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

Therefore the 49-run gate no longer has an implementation/harness blocker. Once raw oracles and source-derived candidate files are available, the complete comparison can run in one command.

## Raw Project files

The two previously missing rasters are located in Project Files:
- `ahn_f250_m.asc` — 23,402,759 bytes;
- `grensvlak_NHIWQ_v2_fill.asc` — 3,521,406 bytes.

Direct raw-byte materialization remains unauthorized in the current runtime. However, both raster contents have now been recovered completely through text line-range materialization and passed a full 1200 x 1300 shape gate. Numerical-content recovery and semantic hashes are recorded in `P12-DRA-R3-RASTER-RECOVERY-2026-09-30.md`.

Therefore the source-raster content blocker is resolved for scientific/numerical reconstruction. Raw-byte identity remains unverified and must not be conflated with numerical-content equivalence.

The earlier 49-run realized DRA set is described in repository authority but is not currently raw-readable in the Library/Project surface. Only one loose raw DRA oracle is currently recoverable:
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

This proves historical dqsat propagation into DRA geometry, but does not discriminate between:
- legacy majority-BFE dqsat selection;
- schema-first representative-SVAT dqsat.

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
- dqsat legacy-vs-schema discrimination;
- nature legacy-vs-schema discrimination;
- SWALLO source-indicator reproduction.

## Admission blocker

Current blocker classification:

**BLOCKER_RAW_49RUN_DRA_AND_REPRESENTATIVE_SVAT_AUTHORITY**

The two source raster numerical contents are no longer blocked. Remaining evidence needed for STATIC04 discrimination is:
1. the persisted 10,242-row Piet representative-SVAT relation, preferably `export_HRUschema_10242.csv` or an exactly equivalent source-bound artifact;
2. `svat.asc` or another exact source-bound SVAT-to-raster-cell relation;
3. the raw 49 realized DRA files for the final multi-run admission gate.

Do not substitute `Runs.col/row` for `svat_repr`: those coordinates represent a different legacy geographic selection and have not been proven to be Piet's hydrologic representative SVAT.

The software needed to compare the resulting candidate set is already present and tested.

Do not infer source rasters or representative-SVAT dqsat from realized DRA outputs. That would make the authority test circular.
