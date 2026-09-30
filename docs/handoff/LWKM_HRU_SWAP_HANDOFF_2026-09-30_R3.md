# LWKM LHM -> SVAT -> HRU -> SWAP handoff R3 — 2026-09-30

## Authority and branch

Repository:
`abhedwig-cell/LWKM`

Work branch:
`work/lhm-hru-swap-workflow-v1`

Head at creation:
`8a85a997193393a2ecd7d662656342268d606904`

Repository remains authority.

This R3 handoff supersedes the operational-status parts of:
- `docs/handoff/LWKM_HRU_SWAP_HANDOFF_2026-09-30_R2.md`;
- `docs/handoff/LWKM_HRU_SWAP_HANDOFF_2026-09-30.md`.

Older handoffs remain useful for source history and rationale.

Before every write:
1. fetch the actual branch head again;
2. read this R3 handoff;
3. read the task-specific authority docs named below.

## Fixed working principles

- Preserve scientific provenance.
- Do not silently repair historical behavior.
- Piet's HRU schema is authority for representative soil, land use and root depth.
- Existing NHI-server Fortran may remain Fortran.
- Batch/orchestration may be modernized.
- LHM/MODFLOW restart mechanics remain upstream responsibility.
- Selective regeneration is required.
- The historical R/SWAPtools route remains a regression oracle until direct-renderer admission.
- Renderer code serializes already-qualified values. It must not redo HRU scientific decisions.

## Closure A — canonical bodem370 lookup

Status:
**CLOSED / QUALIFIED FOR CURRENT PRODUCTION POPULATION**

Persisted:
`config/p12/bodem370_classification_lookup.csv`

Qualification:
- 370 rows;
- 365 realized/qualified codes;
- unobserved exactly `14, 142, 143, 197, 198`;
- deterministic
  `bodem370 -> BOFEK79 -> PAWN21 -> grondsoort4 -> grondsoort2`;
- all ten known historical BOFEK corrections reproduced.

Independent raw source:
historical `SVAT_Waterbalans.xlsx`, sheet `SVAT_INFO`:
- 552,705 total rows;
- `islwkm=1`: 427,656 rows.

Production rule:
representative bodem first, then canonical lookup. Do not re-majority soil2.

Relevant:
- `docs/lhm-hru-swap/P12-BODEM370-LOOKUP-REGENERATION-GATE.md`
- `docs/lhm-hru-swap/H-P12-STATIC03-SOIL2-AUTHORITY.md`

## Closure B — STATIC02 / STATIC03 current-population effects

### STATIC02 SWETR

Schema-first representative land use versus historical Runs.SWETR:
- matches: 10,242 / 10,242;
- mismatches: 0.

Classification:
**DEFECT_CONFIRMED_BUT_CURRENT_POPULATION_NON_DISCRIMINATING for SWETR**.

Nature/DRA4 remains separate because legacy pre-override nature flag is not persisted.

### STATIC03 soil2/crop

Canonical representative-soil lookup versus historical Runs.soil2:
- matches: 10,202;
- mismatches: 40;
- 1 -> 2: 20;
- 2 -> 1: 20.

Downstream crop_id changes:
- 6 runs;
- these are intentional modern authority corrections, not unexplained regression.

Relevant:
- `tools/audit_p12_static_authority.py`
- `docs/lhm-hru-swap/H-P12-STATIC02-LANDUSE-ORDERING.md`
- `docs/lhm-hru-swap/H-P12-STATIC03-SOIL2-AUTHORITY.md`

## Closure C — direct SWP renderer

Status:
**R3 ONE-RUN SERIALIZATION QUALIFIED CANDIDATE**

Run-2000 is fully closed through serialization.

Evidence:
- recovered `Datamodel_10242.sqlite`;
- recovered historical mapping template `swap_wwl.swp`;
- deterministic template adapter;
- explicit `config/swp-profiles/LWKM_2026.yml`;
- raw realized `swap.swp`.

Run-2000 full-active comparison:
- 112 active assignment keys;
- assignment differences: 0;
- crop rotation: 56 / 56 rows equal;
- soil profile: 9 / 9;
- hydraulics: 4 / 4;
- textures: 4 / 4.

Classification:
**RUN_2000_DIRECT_SERIALIZATION_GATE_CLOSED**.

Important architecture:
- direct renderer replaces input serialization only;
- SWAP execution, ZIP lifecycle and post-processing remain separate;
- historical hidden defaults are explicit profile/config values;
- table-header injection previously performed by SWAPtools is explicit in the adapter.

Multi-run tooling is now ready:
- `tools/swp_full_oracle.py`
- `tools/regress_swp_cases.py`

The harness separates:
- exact/semantic equality;
- preregistered expected differences;
- unexplained differences.

Admission still requires realized multi-run evidence.

Relevant:
- `docs/lhm-hru-swap/SWP-REPLACEMENT-IMPLEMENTATION-STATUS.md`
- `docs/lhm-hru-swap/SWP-TEMPLATE-CONTRACT-AUDIT.md`
- `tools/swp_template_adapter.py`
- `tools/swp_full_oracle.py`
- `tools/regress_swp_cases.py`

Current `Template.zip` is now confirmatory, not necessarily a hard production dependency, because a versioned canonical replacement contract exists. If the 49-run regression validates the canonicalized path, the old R/template package can leave the production critical path.

## Closure D — source collection and qualification

Status:
**QUALIFIED IMPLEMENTATION CANDIDATE; REAL NHI Q4 EXECUTION PENDING**

Collection route:
`controls + transfer profile -> resolved plan -> verified v2 bundle`.

Implemented:
- control discovery;
- strict period parsing;
- gap/overlap rejection;
- alias/path resolution;
- configured wildcard expansion;
- annual source completeness;
- explicit raw run-output allowlist;
- SHA-256;
- content-addressed deduplication;
- verified bundle;
- verify-before-unpack;
- immutable snapshot;
- restart payload excluded, lineage preserved.

Qualification route implemented:
`tools/lhm_upstream_qualification.py`

CLI:
```text
python -m tools.lwkm_source_cli qualify \
  --controls <authoritative-run-tree> \
  --profile config/server/lhm433-lwkm-transfer-profile.yml \
  [--bundle bundle.zip] \
  [--output qualification.json]
```

Gate semantics:
- Q0: controls present and parseable;
- Q1: continuous non-overlapping control-period chain;
- Q2: every profile-required source and raw output resolves;
- Q3: required outputs exist, are nonzero, and dated outputs reach period end where timestamps are available;
- Q4: Q0-Q3 PASS plus verified bundle.

LWKM does not repair restart transitions and does not certify MODFLOW numerical correctness.

Relevant:
- `docs/server/LHM-UPSTREAM-RUN-QUALIFICATION.md`
- `docs/server/NHI-TO-LWKM-TRANSFER-CONTRACT.md`
- `docs/server/SERVER-LOGISTICS-STATUS.md`
- `tools/lwkm_source_plan.py`
- `tools/lwkm_source_bundle.py`
- `tools/lwkm_source_cli.py`

## DRA / STATIC04

Status:
**PARTIALLY QUALIFIED; FULL DISCRIMINATING GATE EXTERNALLY BLOCKED**

Run-2000 raw DRA oracle:
- DRARES: 100000, 824, 212, 17040, 30;
- INFRES: 100000, 2498, 725, 100000, 100000;
- L: 100, 80, 80, 80, 80;
- Runs.dqsat = 20;
- systems 2-5: L/4 = 20.

This proves historical dqsat propagation into realized DRA geometry.

It does not discriminate:
- legacy majority-BFE dqsat;
- representative-SVAT dqsat.

A shortcut based only on representative bodem_id is explicitly falsified:
- 249 occurring bodem codes have multiple historical dqsat values;
- max distinct dqsat values per bodem = 15.

Current intended production semantics:
1. representative-SVAT dqsat if valid;
2. otherwise only a separately qualified fallback containing more information than bodem_id alone.

Do not infer representative dqsat from realized L. That would be circular.

Relevant:
- `docs/lhm-hru-swap/P12-DRA-REALIZED-GATE-STATUS.md`
- `docs/lhm-hru-swap/H-P12-STATIC04-DQSAT-ORDERING.md`
- `tools/dra_semantic_oracle.py`

## Raw access rechecked in R3

Located again in Library:
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`.

Raw materialization was retried on the current objects and still fails with:
`Project file does not have an authorized raw-byte materialization path`.

Same class of blocker remains for:
- `run_files.zip` / 49-run realized set;
- current `Template.zip`;
- `control_runs.zip`;
- current Project `SVAT_INFO(1).CSV`.

Do not ask the user to upload these again before checking Project Files/Library in a future runtime.

## Genuine remaining blockers

### B1 Multi-run realized oracle bytes

Need raw `run_files.zip` or equivalent realized run directories.

Blocks:
- 49-run SWP renderer admission;
- 49-run DRA numeric gate;
- nature legacy-vs-schema discrimination;
- representative-SVAT dqsat discrimination.

Software harnesses are ready. This is now an evidence-access blocker.

### B2 DRA raw source rasters

Need raw:
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`.

Blocks:
- exact source-SVAT glk/dqsat reconstruction;
- full ZBOTDR/LEVEL reproduction.

### B3 real authoritative NHI run tree

Needed to execute:
- `lwkm-source qualify`;
- `lwkm-source plan`;
- `lwkm-source collect`;
- verify/unpack;
- consumer smoke test.

Blocks real Q4 source admission and exact authoritative period-chain confirmation.

## CI

Latest fully observed successful suite in this work block:
**135 passed**.

No current implementation-design blocker remains in:
- canonical soil lookup;
- SWP one-run serialization;
- multi-run SWP comparison tooling;
- control-driven source collection;
- Q0-Q4 source qualification.

## Next action when a blocker clears

If 49-run realized cases become raw-readable:
1. run `tools/regress_swp_cases.py`;
2. preregister the six known crop corrections and any other qualified intentional differences;
3. require zero unexplained differences;
4. run DRA oracle comparison over the same cases;
5. close nature/dqsat discrimination;
6. admit renderer if all gates pass.

If DRA rasters become raw-readable:
1. recover representative-SVAT dqsat and glk directly;
2. compare against realized L/4 and DRA depths/levels;
3. close STATIC04 and DRA numeric authority.

If NHI run tree becomes available:
1. qualify Q0-Q3;
2. plan;
3. collect;
4. verify;
5. qualify Q4 with bundle;
6. unpack;
7. smoke-test downstream consumer.

Stop condition for this handoff:
remaining work is constrained by external raw-data/server access, not by unresolved implementation architecture.
