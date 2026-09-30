# LWKM LHM -> SVAT -> HRU -> SWAP handoff R2 — 2026-09-30

## Authority and branch

Repository: `abhedwig-cell/LWKM`

Work branch:
`work/lhm-hru-swap-workflow-v1`

Head at this handoff:
`f5609de631273735c03dd8545095bcec17482d2e`

Repository remains authority. This R2 handoff supersedes the operational-status parts of:
`docs/handoff/LWKM_HRU_SWAP_HANDOFF_2026-09-30.md`.

The older handoff remains useful for historical decisions and source context.

## Working principles

Unchanged:
- preserve scientific provenance;
- do not silently repair historical behavior;
- Piet's HRU schema is authority for representative soil, land use and root depth;
- existing NHI-server Fortran may remain Fortran;
- batch/orchestration may be modernized;
- LHM/MODFLOW restart mechanics remain upstream responsibility;
- selective regeneration is required;
- Martin's R/template path remains regression oracle until direct renderer admission.

Before every write:
1. fetch branch head;
2. read this R2 handoff;
3. read task-specific authority docs.

## Major closure 1 — canonical bodem370 classification lookup

Status:
**CLOSED / QUALIFIED FOR CURRENT PRODUCTION POPULATION**

Persisted:
`config/p12/bodem370_classification_lookup.csv`

Qualification:
- 370 rows total;
- 365 realized/qualified codes;
- exactly five unobserved codes:
  `14, 142, 143, 197, 198`;
- deterministic mapping:
  `bodem370 -> BOFEK79 -> PAWN21 -> grondsoort4 -> grondsoort2`;
- ten known historical BOFEK corrections reproduced exactly.

Independent raw source recovery:
- `Datamodel_9830.zip`, historical archive;
- extracted `SVAT_Waterbalans.xlsx`, sheet `SVAT_INFO`;
- 552,705 source rows;
- `islwkm=1` population = 427,656 rows.

Relevant docs/code:
- `docs/lhm-hru-swap/P12-BODEM370-LOOKUP-REGENERATION-GATE.md`
- `docs/lhm-hru-swap/P12-BODEM370-BOFEK-LOOKUP-AUTHORITY.md`
- `tools/build_bodem370_lookup.py`
- `tests/test_bodem370_lookup.py`

Important hashes:
- `Datamodel_10242.sqlite`:
  `4b697e7f806d0e6f0c345b92bb78c456238c3af5634559a7e2f7edd4171183bb`
- historical extracted `Datamodel_10242.xlsx`:
  `5a4e68cb958cb8187639db7750e957c509caf67f81b5b11096c929ca796244d8`

## Major closure 2 — STATIC02 representative-landuse impact

Status:
**SWETR CURRENT-POPULATION EFFECT = ZERO**

Across all 10,242 Runs:
- legacy emitted SWETR 0 and representative-derived SWETR 0: 7,162;
- legacy emitted SWETR 1 and representative-derived SWETR 1: 3,080;
- mismatch: **0 / 10,242**.

Therefore the source ordering defect is real, but current production is non-discriminating for SWETR.

Nature/DRA4 remains separate and not closed across 49 runs.

Relevant:
- `docs/lhm-hru-swap/H-P12-STATIC02-LANDUSE-ORDERING.md`
- `tools/audit_p12_static_authority.py`
- `tests/test_audit_p12_static_authority.py`

## Major closure 3 — STATIC03 soil2/crop authority impact

Status:
**QUALIFIED INTENTIONAL MODERN CORRECTION**

Across all 10,242 Runs, canonical representative-soil lookup versus historical Runs.soil2:
- exact match: 10,202;
- soil2 mismatch: **40**;
- 1 -> 2: 20;
- 2 -> 1: 20;
- missing canonical lookup: 0.

Using canonical soil2 + representative land use changes crop_id in **6 runs**:
- 6050: 26 -> 6;
- 8139: 6 -> 26;
- 9378: 6 -> 26;
- 9612: 26 -> 6;
- 9822: 26 -> 6;
- 9824: 26 -> 6.

These are expected authority corrections, not unexplained renderer regressions.

Relevant:
- `docs/lhm-hru-swap/H-P12-STATIC03-SOIL2-AUTHORITY.md`
- `tools/audit_p12_static_authority.py`

## Major closure 4 — direct SWP renderer context layer

Status:
**QUALIFIED R2 CONTEXT CANDIDATE**

Recovered raw historical datamodel:
`Datamodel_10242.sqlite`

10,242-run audit gives zero missing joins for:
- discretisatie;
- eigenschappen;
- crop rotation;
- Output;
- Gewasweerstand;
- Scenario;
- DZNEW count versus NUMNODNEW;
- ELAS.

RDS authority:
- Runs.RDS is production authority;
- Wortelzone.RDS is QA only;
- 4,350 / 10,242 historical Wortelzone mismatches do not override Runs.

Run-2000 raw oracle:
- `swap.swp` SHA-256
  `6b47cec011749041bc99e78322ed99a4116b798ec67536969074984f96a49796`;
- `2000.bbc` SHA-256
  `fe1aa408e2be00ae261dfe1f9244a682d525707e24aef63da421e6f134bafc1c`;
- `2000.dra` SHA-256
  `85dff23754d138b12e3084e5c06c6ad3eb77880c64d7a24f85aa48aae4acd15e`;
- `2000.met` SHA-256
  `2598998b5c161aedb9d39c6e3ea8919c78b9a9efbf909506f2a0dfa163a5a8f4`.

Implemented:
- context builder;
- semantic SWP oracle;
- context-to-oracle comparison;
- selective dependency fingerprinting;
- one-run semantic fixture.

Relevant:
- `docs/lhm-hru-swap/P12-DIRECT-RENDERER-R2-CONTEXT-QUALIFICATION.md`
- `docs/lhm-hru-swap/SWP-REPLACEMENT-IMPLEMENTATION-STATUS.md`
- `tools/swp_context.py`
- `tools/swp_semantic_oracle.py`
- `tools/compare_swp_context.py`
- `tools/compare_swp_semantics.py`
- `tools/swp_fingerprint.py`

Admission still blocked by:
1. current production template bytes or an explicitly versioned canonical replacement;
2. full 49-run realized SWP regression.

Historical `swap_wwl.swp` is mapping-oracle only. It hard-codes SWETR=0 and cannot be current production authority because 3,080 current Runs require SWETR=1.

## Major closure 5 — NHI/LHM source collector

Status:
**QUALIFIED IMPLEMENTATION CANDIDATE, REAL-SERVER Q4 PENDING**

Implemented route:
`control files + transfer profile -> resolved plan -> verified v2 bundle`

CLI:
```text
python -m tools.lwkm_source_cli plan --controls <run-tree> --profile config/server/lhm433-lwkm-transfer-profile.yml --output plan.json

python -m tools.lwkm_source_cli collect --controls <run-tree> --profile config/server/lhm433-lwkm-transfer-profile.yml --output bundle.zip
```

Implemented:
- recursive control discovery;
- period gap/overlap rejection;
- alias/path resolution;
- wildcard expansion;
- annual-source completeness;
- explicit raw run-output allowlist;
- SHA-256;
- content-addressed deduplication;
- verify-before-unpack;
- immutable snapshot;
- restart payload excluded, lineage preserved in controls.

Relevant:
- `docs/server/SERVER-LOGISTICS-STATUS.md`
- `docs/server/NHI-TO-LWKM-TRANSFER-CONTRACT.md`
- `config/server/lhm433-lwkm-transfer-profile.yml`
- `tools/lwkm_source_plan.py`
- `tools/lwkm_source_bundle.py`
- `tools/lwkm_source_cli.py`

Q4 requires one real run on the authoritative NHI/LHM run tree.

## DRA / STATIC04 status

Status:
**PARTIALLY QUALIFIED; FULL 49-RUN GATE BLOCKED**

Run-2000 DRA oracle persisted:
`tests/fixtures/dra/run_2000_dra_oracle.json`

Parser:
`tools/dra_semantic_oracle.py`

Run 2000:
- DRARES: 100000, 824, 212, 17040, 30;
- INFRES: 100000, 2498, 725, 100000, 100000;
- L: 100, 80, 80, 80, 80;
- Runs.dqsat = 20;
- L/4 = 20 for systems 2-5.

This proves realized DRA propagation from the historical dqsat intermediate, but does not discriminate legacy-majority versus representative-soil dqsat authority.

Relevant:
- `docs/lhm-hru-swap/P12-DRA-REALIZED-GATE-STATUS.md`
- `docs/lhm-hru-swap/H-P12-STATIC04-DQSAT-ORDERING.md`

## Raw-file access status

Raw-readable/recovered in the working runtime during this chat:
- `source (2).zip`;
- `exe.zip`;
- historical `Datamodel_9830.zip` sufficiently to recover datamodel artifacts;
- `Datamodel_10242.sqlite`;
- historical `Datamodel_10242.xlsx`;
- `SVAT_Waterbalans.xlsx`;
- `swap.swp`;
- `2000.bbc`;
- `2000.dra`;
- `2000.met`.

Located but current Project backing bytes remain unauthorized:
- `control_runs.zip`;
- `Tools.zip`, `Tools(1).zip`, `Tools(2).zip`;
- `Template.zip`;
- `run_files.zip` containing the earlier 49-run oracle set;
- `run_000000012.zip`;
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`;
- current Project `SVAT_INFO(1).CSV`.

Do not ask the user to re-upload these before rechecking Library/Project access.

## Genuine remaining blockers

### B1 49-run raw oracle access
Need raw access to `run_files.zip` or equivalent realized run directories.

Blocks:
- 49-run DRA numeric gate;
- nature legacy-vs-schema discrimination;
- dqsat authority discrimination;
- full SWP 49-run renderer regression.

### B2 DRA source raster raw access
Need raw:
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`.

Blocks exact ZBOTDR/LEVEL and dqsat-source reconstruction.

### B3 current template raw access
Need `Template.zip` or deliberate canonical-template replacement admission.

Blocks complete direct-renderer serialization admission.

### B4 real NHI server execution
Need collector execution on original authoritative run tree.

Blocks Q4 source-bundle admission and exact control-period chain confirmation.

## Immediate next work when any blocker is removed

If `run_files.zip` becomes raw-readable:
1. extract 49 DRA/SWP/BBC/MET oracles;
2. run shared regression harness;
3. classify every discriminating case.

If DRA rasters become readable:
1. reconstruct glk/dqsat per source SVAT;
2. run DRA numeric gate;
3. close nature/dqsat discrimination where oracles exist.

If Template.zip becomes readable:
1. inventory actual tokens and R side effects;
2. bind to current typed context;
3. render run 2000;
4. require semantic identity;
5. expand to 49 runs.

If authoritative NHI run tree is available:
1. run `lwkm-source plan`;
2. inspect exact period chain;
3. run `collect`;
4. verify/unpack;
5. smoke-test downstream consumers.

## CI

At R2 handoff, branch CI is green through the latest implemented audits/oracles.

Stop condition for this work block:
qualified results have been produced and remaining work is constrained by explicit raw-data/server blockers rather than unresolved implementation design.
