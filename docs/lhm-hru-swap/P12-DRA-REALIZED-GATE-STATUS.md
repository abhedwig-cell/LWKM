# P12 DRA realized reproduction gate status

Status:
**PARTIALLY QUALIFIED, 49-RUN NUMERIC GATE BLOCKED BY RAW-ORACLE ACCESS**

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

## Raw Project files

The two previously missing rasters are located in Project Files:
- `ahn_f250_m.asc` — 23,402,759 bytes;
- `grensvlak_NHIWQ_v2_fill.asc` — 3,521,406 bytes.

Their backing bytes are still not authorized for materialization in the current runtime. This is an access limitation, not evidence that the files are absent.

The earlier 49-run realized DRA set is described in repository authority but is no longer available as individually raw-readable `.dra` files in the current Library surface. Only one loose raw DRA oracle is currently recoverable:
- `2000.dra`;
- SHA-256 `85dff23754d138b12e3084e5c06c6ad3eb77880c64d7a24f85aa48aae4acd15e`.

Therefore the full 49-run numeric admission gate cannot be completed without recovering that oracle set or equivalent raw data.

## Independent run-2000 DRA oracle

Observed realized values:

| system | DRARES d | INFRES d | L cm | ZBOTDR cm | SWALLO |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 100000 | 100000 | 100 | 0.00 | 3 |
| 2 | 824 | 2498 | 80 | -97.79 | 1 |
| 3 | 212 | 725 | 80 | -100.00 | 3 |
| 4 | 17040 | 100000 | 80 | -50.06 | 3 |
| 5 | 30 | 100000 | 80 | -24.17 | 3 |

This independently supports two already reconstructed behaviors:
- systems 4 and 5 have `INFRES = 100000` in the realized file;
- active systems 2-5 all use `L = 80 cm`.

The recovered `Datamodel_10242.xlsx` row for run 2000 contains:
- `dqsat = 20`.

Hence:
`L / 4 = 20 = Runs.dqsat`

for systems 2-5.

This confirms that the realized DRA producer and the Runs intermediate used the same dqsat value for run 2000. It does **not** yet discriminate between:
- legacy majority-BFE dqsat selection;
- schema-first representative-soil dqsat semantics.

The representative candidate still requires the raw dqsat/member authority.

## Nature discrimination

Run 2000 has final representative `lu_id = 1`, therefore schema-first `isnatuur = false`.

Its realized system 4 has:
- raw/effective DRARES4 = 17040, below the independent >20000 shutdown criterion;
- nonzero drainage depth;
- therefore system 4 is not nature-suppressed.

This is consistent with the representative-landuse hypothesis but is non-discriminating because the legacy majority nature classification for this HRU is not independently available.

## What is already qualified

Qualified:
- DRA serialization shape;
- system ordering;
- all-member support rule;
- DRARES/INFRES algebra in unit tests;
- run-2000 dqsat propagation from Runs to realized L;
- run-2000 system-4 state is physically consistent with representative non-nature land use.

Not yet qualified across the 49-run oracle:
- exact DRARES/INFRES numeric reproduction;
- ZBOTDR/LEVEL reproduction;
- dqsat legacy-vs-schema discrimination;
- nature legacy-vs-schema discrimination;
- SWALLO source-indicator reproduction.

## Admission blocker

The blocker is now narrow and external to the implemented formulas:

**BLOCKER_RAW_49RUN_DRA_AND_SOURCE_RASTER_BYTES**

To close the gate, recover raw access to:
1. the 49 realized `.dra` files;
2. `ahn_f250_m.asc`;
3. `grensvlak_NHIWQ_v2_fill.asc`.

Do not infer these source grids from realized outputs. That would make the admission test circular.
