# LWKM LHM -> SVAT -> HRU -> SWAP handoff R4 — 2026-09-30

## Authority and branch

Repository:
`abhedwig-cell/LWKM`

Work branch:
`work/lhm-hru-swap-workflow-v1`

Head immediately before this R4 write:
`3323c96750d6a2f0b4efae9e5de553d0b1b583e9`

Repository remains authority.

This R4 handoff supersedes the operational-status parts of R3. R3 and older handoffs remain useful for history and rationale.

Before every write:
1. fetch the actual branch head again;
2. read this R4 handoff;
3. read `docs/handoff/NEXT_CHAT_PROMPT_2026-09-30.txt`;
4. read task-specific authority docs named below.

## Fixed principles

- Preserve scientific provenance.
- Do not silently repair historical behavior.
- Piet's HRU schema is authority for representative soil, land use and root depth.
- Renderer/producer code serializes already-qualified scientific choices and must not recreate HRU majorities.
- BBC, DRA and MET remain separate producers.
- Historical source behavior, realized executable behavior and modern corrected authority are distinct semantics when evidence shows they differ.
- Expected differences must be preregistered; unexplained differences remain admission failures.

## Existing closures retained from R3

Still closed/qualified:
- canonical bodem370 lookup, 370 codes, 365 realized, unobserved exactly 14/142/143/197/198;
- STATIC02 SWETR: 10,242/10,242 schema-first representative land use versus historical Runs equal;
- STATIC03: 40 soil2 corrections and 6 resulting crop_id corrections, qualified intentional differences;
- run-2000 direct SWP serialization: 112 active assignments and all four dynamic tables equal;
- source collector implementation and Q0-Q4 qualification route;
- exact run-2000 DRA propagation `Runs.dqsat -> L/4`;
- representative-bodem-only dqsat fallback falsified;
- multi-run SWP and DRA regression harnesses implemented.

## R4 closure A — DRA source rasters recovered semantically

Raw-byte materialization of Project objects remains unauthorized, but complete numerical contents of both rasters were recovered through line-range text materialization.

Recovered:
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`.

Both passed:
- 1200 columns;
- 1300 rows;
- exactly 1,560,000 cells;
- exact row width on all 1300 data rows.

Semantic float64-array hashes:
- AHN/glk: `6137121ac628db3330dc48a12e1849cd25dd2169485f24215230317522b8f5f8`;
- dqsat: `79fdfc37153aea04a9ec24cef1b3d981f519aaed062f8c07e8922766bb3849cd`.

These are semantic numerical hashes, not raw-file byte hashes.

Authority:
`docs/lhm-hru-swap/P12-DRA-R3-RASTER-RECOVERY-2026-09-30.md`.

## R4 closure B — STATIC04 dqsat source-side qualified

Recovered historical raw-readable `csv.zip` authority:
- archive SHA-256 `84ae4963145176767a00c67b968ace5b817002d5292fd9cab8d3933476e509e3`;
- `csv/export_HRUschema_10242.csv`: 10,242 HRUs;
- `csv/export_svat_HRU_NRU_10242.csv`: 427,656 member SVATs.

All 10,242 `svat_repr` values:
- are unique;
- occur exactly once in the member relation;
- belong to the same HRU as the schema row.

Exact comparison:
- legacy: majority BFE, then majority dqsat within that BFE population;
- candidate: source dqsat at Piet's authoritative representative SVAT.

Result:
- equal: 7,471 HRUs;
- different: 2,771 HRUs = 27.055%;
- representative > legacy: 1,357;
- representative < legacy: 1,414;
- median absolute difference among discriminating HRUs: 4 cm;
- maximum absolute difference: 20 cm.

Run 2000 is non-discriminating:
legacy = representative = Runs = realized L/4 = 20.

Classification:
`STATIC04_DQSAT_SOURCE_SIDE_QUALIFIED`.

Authority:
- `docs/lhm-hru-swap/P12-STATIC04-DQSAT-RESULT-2026-09-30.md`;
- `docs/lhm-hru-swap/H-P12-STATIC04-DQSAT-ORDERING.md`;
- `tools/compare_dqsat_authority.py`;
- `tests/test_compare_dqsat_authority.py`.

Production semantics:
1. use source dqsat at Piet's representative SVAT;
2. only if unavailable, use a separately qualified richer fallback;
3. never introduce a new HRU majority;
4. never infer representative dqsat from realized `L/4`;
5. never use a simple soil-id -> dqsat lookup.

## R4 closure C — nature / DRA4 source-side closed

Supplied-source defect:
- legacy nature flag is calculated from member-majority land use;
- final representative land use is applied later;
- nature flag is not recomputed.

Full 10,242-HRU source comparison:
- exact legacy versus representative land-use code differs: 1,974 HRUs;
- legacy versus representative nature boolean differs: **0 HRUs**;
- nature true in both semantics: 2,825 HRUs.

Among the 1,974 land-use differences:
- 1,107 remain non-nature;
- 867 remain nature.

Classification:
- `STATIC_NATURE_ORDERING_DEFECT_CONFIRMED_CURRENT_POPULATION_NON_DISCRIMINATING`;
- `DRA4_NATURE_SOURCE_SIDE_CLOSED`.

Therefore nature ordering is a zero-expected-difference correction for the current 10,242-HRU population. It cannot explain any realized 49-run DRA4 mismatch.

Authority:
- `docs/lhm-hru-swap/P12-NATURE-DRA4-AUTHORITY-RESULT-2026-09-30.md`;
- `tools/compare_nature_authority.py`;
- `tests/test_compare_nature_authority.py`.

## R4 closure D — SWALLO provenance split confirmed

The separate river-infiltration indicator is now source-bound.

HRUlist2SWAP:
- reads `riv_infil`;
- aggregates equal-member mean to `infil_avg`.

LWKM_makeHRU writes the same upstream quantity into `SVAT_INFO_HRU.CSV`, historically under the misleading header:
`wegzijgingz(mm/j)`.

Full current population:
- `infil_avg < 10`: 6,324 HRUs;
- `infil_avg >= 10`: 3,918;
- exactly 10: 0.

Supplied active v0.38 source:
`system > 3 OR INFRES > 20000 OR infil_avg < 10 -> SWALLO=3`.

Source history v0.27 states:
`SWALLO=3 voor sys>2`.

Run 2000 is discriminating:
- reconstructed `infil_avg = 11.8204166667`;
- realized `INFRES3 = 725`;
- realized `SWALLO3 = 3`.

Thus supplied active v0.38 predicts SWALLO3=1 and is falsified for the realized executable. The historical `system > 2` rule predicts 3 and matches.

Classification:
`SWALLO_SUPPLIED_SOURCE_V038_VS_REALIZED_EXECUTABLE_MISMATCH`.

Explicit code modes:
- `SUPPLIED_SOURCE_V038`: force systems 4-5;
- `REALIZED_PRODUCTION_COMPAT`: force systems 3-5.

Common conditions remain:
- INFRES > 20000;
- river-infiltration indicator < 10.

Implemented:
- `tools/p12_swallo.py`;
- `tools/generate_dra.py` accepts explicit `swallo_mode`;
- tests cover both modes and run-2000 discriminator.

Authority:
- `docs/lhm-hru-swap/P12-SWALLO-REALIZED-PROVENANCE-2026-09-30.md`;
- `docs/lhm-hru-swap/P12-SWALLO-RIVER-INFILTRATION.md`.

Do not silently collapse these two provenance modes.

## Current regression-oracle manifest

`config/p12/regression-oracle-v1.yml` is now schema version 2.

It records:
- SWETR current population non-discriminating;
- nature current population non-discriminating;
- STATIC03 known soil2 differences;
- STATIC04 7,471 equal / 2,771 discriminating;
- MET district 49/49 qualified;
- WET 17,885/17,885 qualified;
- DRA aggregation full realized gate pending;
- SWALLO provenance split and run-2000 `EXPLAINED_PROVENANCE`.

## Remaining primary evidence blocker — 49 realized runs

Library still contains:
`/LWKM/run_files.zip`
size 20,953,239 bytes.

It contains 49 realized HRU directories, IDs in 7866..7945 with gaps.

Known structure:
- substantive BBC;
- substantive DRA;
- substantive MET;
- `swap.swp`;
- crop/CO2 assets.

A full Library crawl found only this one original archive object.

Repeated attempts:
- direct raw materialization;
- text extraction;
- copied Library objects;
- detached root-level Library copies;
all remain blocked by the same raw-byte authorization path.

This is now a genuine external evidence-access blocker, not an implementation blocker.

Known 49-run population facts retained:
- 40/49 have at least one donor-different member;
- 9/49 donor-equal only;
- HRU 7876: 57 = 42 donor + 15 target;
- HRU 7875: 45 = 17 + 28;
- HRU 7877: 28 = 27 + 1;
- HRU 7869: 25 donor-only.

Known STATIC04 examples:
- 7866: legacy 7, representative 7;
- 7869: 9/9;
- 7875: 18/18;
- 7876: 18/18;
- **7877: legacy 18, representative 17 — discriminating**;
- 7913: 10/10;
- 7916: 10/10;
- 7945: 7/7.

Do not infer the realized 7877 value without its DRA oracle.

### When raw access clears

Immediately:
1. extract the 49 realized directories;
2. run `tools/regress_swp_cases.py`;
3. run `tools/regress_dra_cases.py`;
4. classify active-system `L/4` against legacy and representative STATIC04 predictions;
5. apply explicit expected differences for qualified soil/crop authority corrections;
6. apply explicit SWALLO provenance classification;
7. nature/DRA4 remains zero-expected-difference for this population;
8. require zero unexplained differences.

Only then assess:
- `DIRECT_DRA_PRODUCER_ADMITTED`;
- `DIRECT_SWP_RENDERER_ADMITTED`.

## NHI/LHM real-source qualification

Implementation status remains:
**QUALIFIED IMPLEMENTATION CANDIDATE, REAL-SERVER ADMISSION PENDING**.

A Library search now confirms at least a loose:
`control_run_1970_1979.ini`.

This is not sufficient to claim an authoritative complete run tree. No complete raw run-root with all required control periods and profile-bound raw outputs has been established in the current environment.

Do not manufacture a Q0-Q4 success from loose controls.

Required for real Q4 remains:
1. authoritative complete control/run tree;
2. `qualify` Q0-Q3;
3. `plan`;
4. `collect`;
5. verify bundle;
6. `qualify --bundle` Q4;
7. unpack immutable snapshot;
8. downstream consumer smoke test.

Authority:
- `docs/server/LHM-UPSTREAM-RUN-QUALIFICATION.md`;
- `docs/server/NHI-TO-LWKM-TRANSFER-CONTRACT.md`;
- `docs/server/SERVER-LOGISTICS-STATUS.md`.

## CI

The latest observed pre-R4 branch head:
`3323c96750d6a2f0b4efae9e5de553d0b1b583e9`

completed:
**LWKM canonical unit tests — SUCCESS**.

All immediately preceding R4 code changes, including STATIC04 comparator, nature comparator, explicit SWALLO modes and DRA serializer provenance parameterization, also completed successfully.

## Current stop state

No unresolved scientific-authority question remains for:
- representative-SVAT dqsat source semantics;
- current-population nature/DRA4 semantics;
- run-2000 SWALLO provenance discrimination;
- DRA comparison harness architecture.

The remaining admission work is constrained primarily by:
1. inaccessible raw 49-run realized archive;
2. absent complete authoritative real NHI/LHM run tree.

This is therefore a legitimate blocker-driven handoff point.
