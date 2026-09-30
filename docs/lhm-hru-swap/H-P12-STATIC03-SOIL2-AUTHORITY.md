# H-P12-STATIC03 — soil2 authority resolution

## Resolved semantics

soil2 / grondsoort2 is a deterministic lookup-derived soil class, not an independent HRU decision.

Canonical hierarchy:
`bodem370 -> BOFEK79 -> PAWN21 -> grondsoort4 -> grondsoort2`.

The canonical 370-row lookup is now persisted in:
`config/p12/bodem370_classification_lookup.csv`.

Source qualification is documented in:
`P12-BODEM370-LOOKUP-REGENERATION-GATE.md`.

## Legacy behavior

The historical Fortran computes:
`soil2_maj = MAJORITY(member soil2)`

and later combines it with the final representative land use for crop mapping.

That is a second HRU-level reduction after soil classification already exists upstream and can therefore disagree with the representative soil authority.

Classification:
**LEGACY_AUTHORITY_REDUCTION_SUPERSEDED_BY_SCHEMA_FIRST_LOOKUP**.

## 10,242-run impact audit

Inputs:
- recovered `Datamodel_10242.sqlite`, SHA-256
  `4b697e7f806d0e6f0c345b92bb78c456238c3af5634559a7e2f7edd4171183bb`;
- canonical lookup generated from the realized SVAT population.

At the typed Runs boundary:
- `Runs.bodem_id` is the final representative soil identity;
- `Runs.soil2_id` is the historical/member-majority coarse class.

For every run the schema-first candidate was calculated as:
`canonical_lookup[Runs.bodem_id].grondsoort2`.

Result:
- exact soil2 agreement: **10,202 / 10,242**;
- mismatch: **40 / 10,242**, about **0.39%**;
- direction 1 -> 2: **20**;
- direction 2 -> 1: **20**;
- missing canonical lookup for the production Runs population: **0**.

The 40 mismatches occur across 27 representative soil codes. The largest groups are:
- bodem 97: 4 runs;
- bodem 145: 4 runs;
- bodem 61: 3 runs;
- bodem 200: 3 runs;
- bodem 36, 199 and 202: 2 runs each.

All other affected representative soil codes occur once.

The audit is reproducible through:
`tools/audit_p12_static_authority.py`.

## Downstream crop impact

The recovered SQLite also contains the `lu2crop` domain lookup.

Recomputing crop_id from:
- canonical representative soil2;
- final representative `Runs.lu_id`;

changes crop_id in **6 of 10,242 runs**:

| run_id | bodem_id | historical soil2 | canonical soil2 | lu_id | historical crop_id | canonical crop_id |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6050 | 364 | 1 | 2 | 2 | 26 | 6 |
| 8139 | 61 | 2 | 1 | 2 | 6 | 26 |
| 9378 | 157 | 2 | 1 | 2 | 6 | 26 |
| 9612 | 201 | 1 | 2 | 2 | 26 | 6 |
| 9822 | 199 | 1 | 2 | 2 | 26 | 6 |
| 9824 | 199 | 1 | 2 | 2 | 26 | 6 |

The other 34 soil2 mismatches do not change crop_id because their land-use class maps both coarse soil classes to the same crop.

## Production consequence

The historical member-majority soil2 must not be retained merely for byte-level compatibility.

Modern production must:
1. take the authoritative representative soil/bodem identity;
2. resolve soil2 through the canonical lookup;
3. use that canonical soil2 for crop mapping;
4. record the 40 soil2 and 6 crop changes as intentional authority corrections.

Member-majority soil2 remains available only as a regression/QA diagnostic.

The 6 crop changes are expected modern differences, not unexplained renderer regressions.
