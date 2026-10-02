# LWKM LHM -> SVAT -> HRU -> SWAP handoff R6 — 2026-10-02

## Authority and branch

Repository:
`abhedwig-cell/LWKM`

Work branch:
`work/lhm-hru-swap-workflow-v1`

Head immediately before this R6 write:
`3692a0d90cc3e7f46e4e2a012d24fc2eb12d1c67`

Repository remains authority.

This R6 handoff supersedes the operational-status and priority sections of R5. R5 and older handoffs remain useful for history, rationale and already qualified evidence.

Before every write:
1. fetch the actual branch head again;
2. read this R6 handoff;
3. read `docs/handoff/NEXT_CHAT_PROMPT_2026-09-30.txt`;
4. read the task-specific authority documents named below.

## Executive state

The reconstruction has moved beyond basic archaeology. The main LHM -> SVAT -> HRU -> SWAP workflow is substantially understood and several source, mapping and regression gates are closed. The remaining blockers are now concentrated in historical provenance and end-to-end qualification rather than in the basic workflow structure.

The most important distinction remains:

1. **supplied-source semantics**: what the recovered source files literally contain;
2. **realized executable semantics**: what the historical 49-run outputs demonstrably did;
3. **modern corrected production semantics**: what the new Python-based production route should intentionally do.

Do not collapse these layers.

## What is already qualified or implemented

### Datamodel and HRU context

The current authoritative workbook `Datamodel_10242.xlsx` has been recovered and ingested directly.

Qualified:
- SHA-256 `5a4e68cb958cb8187639db7750e957c509caf67f81b5b11096c929ca796244d8`;
- 22 worksheets;
- 10,242 Runs;
- 10,242 typed execution contexts;
- zero unresolved joins or required-field issues;
- 337,098 formula cells have stored values.

SQLite is only an execution representation of the workbook. It is not separate scientific authority.

The old `Datamodel_9830.zip` is excluded and must not be used.

Authority:
`docs/lhm-hru-swap/P12-XLSX-RECOVERY-DRA-DIAGNOSTIC-2026-10-01.md`.

### Raw 49-run historical oracle

`run_files(1).zip` is recovered and qualified as the realized historical test oracle.

SHA-256:
`46f1fc6b6f4aa01265db950c8ca78f9c4714a97d11cfa4d8f0c66b4dea7a05e3`.

It contains exactly 49 realized HRU runs with SWP, DRA, BBC and MET assets.

The former raw-49-run blocker is closed.

### STATIC04 drainage-spacing behavior

The 49-run realized DRA comparison closes the historical dqsat question for drainage spacing:

- 34 runs non-discriminating;
- 15 runs follow the legacy majority-BFE dqsat;
- zero unexplained STATIC04 cases.

Modern production authority remains **representative-SVAT dqsat**.

Therefore 75 modern DRA `L` differences are expected and preregistered:
15 runs x 5 systems.

Authority:
`docs/lhm-hru-swap/P12-49RUN-STATIC04-REALIZED-RESULT-2026-10-01.md`
and
`config/p12/dra-49run-static04-expected-differences-v1.yml`.

### SWALLO

For the 49-run historical archive:
- supplied v0.38 SWALLO policy matches 241/245 values;
- 47/49 runs match completely;
- residual historical cases remain HRU 7868 systems 1/2 and HRU 7929 systems 2/3;
- universal forced SWALLO=3 for systems 3-5 is falsified.

v0.38 is a behavioral baseline only, not proven binary identity.

### DRA comparator

The DRA regression gate now checks:
- DRARES;
- INFRES;
- ZBOTDR;
- SWALLO;
- every seasonal LEVEL date/value;
- extra/missing assignments.

This repaired a real comparator gap.

### Python LHM server post-processing

Implemented:
- `tools/lhm_postprocess.py`;
- strict IDF handling for the qualified layout;
- flux aggregation and MODFLOW m3 -> mm conversion;
- positive/negative sign split;
- state averaging;
- ASCII combine/mean;
- strict geometry/NODATA handling;
- tests.

Target architecture is Python for downstream orchestration and deterministic raster calculations, while MODFLOW/MetaSWAP themselves remain external model engines.

Production admission still requires a small real-server golden regression.

Authority:
`docs/server/LHM433_PYTHON_POSTPROCESSING_MIGRATION_2026-09-30.md`.

## Direct SWP renderer status

The current XLSX path is no longer blocked.

The remaining SWP blocker is the historical mapping template/profile.

Expected historical template:
`swap_wwl.swp`

Expected SHA-256:
`d960f7ede8074672f8f8d6c938df0554383f631e75dfdb67ea33bfe15cc5beab`.

The recovered current `Template/wwl.swp` is a different version:
SHA-256
`ee0c23696fd5565a4b99eb81ce469a1be7c86494cfb20545dfba492820a5858a`.

Important incompatibilities include PERIOD=1 instead of the adapter's qualified PERIOD=0 expectation and other template-structure differences.

A real regression attempt with the current template fails before rendering:
`expected exactly one active PERIOD=0 assignment`.

This is an honest incompatibility, not a reason to weaken the gate.

Recovery already covered:
- full Library catalog;
- exact-name/hash searches;
- previous conversation evidence;
- 30 nested alternate archives;
- current Template.zip;
- Tools(2).zip;
- LWKM_workflow_no_asc.zip;
- source and R-script archives.

No exact historical template has been recovered.

Status:
`DIRECT_SWP_RENDERER_ADMITTED = false`.

## Direct DRA producer status

### Modern production authority

Retain:
- deterministic all-member aggregation;
- full 62,500 m2 MODFLOW cell support per HRU member;
- representative-SVAT dqsat;
- no emulation of undefined Fortran state;
- no force-fitting to historical outputs.

### Independent source diagnostic

Using current membership, recovered AHN and recovered drainage/infiltration rasters, a diagnostic-only comparison against all 49 realized DRA files gives, over 245 systems:

- DRARES mismatches: 226;
- INFRES mismatches: 133;
- ZBOTDR mismatches: 230;
- seasonal LEVEL mismatches: 230;
- SWALLO mismatches: 3.

These differences are not admitted intentional differences.

This diagnostic rules out simple rounding and the single-current-representative-cell hypothesis as general explanations.

### Supplied-source defect

All four supplied Alterratools variants have the same `AVERAGE` defect for N>1:
the function result is read before initialization.

Qualified result:
`SUPPLIED_AVERAGE_READ_BEFORE_INITIALIZATION_CONFIRMED`.

This does **not** prove:
- which implementation was linked historically;
- which compiler/runtime behavior occurred;
- that the defect caused the realized DRA differences.

Modern production must remain deterministic.

### Run-linked producer provenance

A supplied production batch now binds the 10,242-run workflow to:

```bat
exe\HRU2SWAP.exe HRUSWAP_test.log control_LHM433_HRU_SWAP_10242.inp
```

and then:
```bat
cd svats10242
do_kopybbcdra.bat
```

This establishes expected runtime executable and log filenames, not binary/source identity.

The control file explicitly binds:
- WQ model = SWAP;
- SWAP_model_dir = SVATS10242;
- SWAP_model_name = SVAT2SWAP10242;
- DRA = Yes;
- MET = No;
- BOT = No;
- TimStart = 19710101;
- TimEnd = 20211231;
- dqsat source;
- the three length-grid names;
- drainage conductance, infiltration, bottom and seasonal-level paths.

Authority:
`docs/lhm-hru-swap/P12-RUN-LINKED-PRODUCER-PROVENANCE-FOLLOWUP-2026-10-02.md`.

### Historical version chronology

All 49 realized DRA members have ZIP member timestamp:
`2026-03-24 20:56:36`.

Current supplied source history states:
- v0.35: Mar-26, new suspect-cell implementation;
- v0.36: Mar-26, new suspect-cell implementation;
- v0.37: Apr-26, irrigation threshold change;
- v0.38: Apr-26, drainage-resistance bugfix for selected cells.

The current source identifies itself as v0.38 Apr-2026.

ZIP timestamps and source-history labels are mutable provenance clues, not authenticated build dates. Therefore they do not prove v0.35 or v0.36, but an exact v0.38 replay is chronologically unsupported.

A pre-v0.38 selected-member route is now the highest-value historical hypothesis.

The v0.38 source contains commented traces of older selected-member handling:
- `issvatwb(jj)` inclusion guards;
- `nusvatwb`;
- `areawb_sum`.

These traces are not enough to reconstruct exact v0.35/v0.36 behavior.

No loose v0.35/v0.36/v0.37 source, historical producer log, `HRU2SWAP.exe`, `HRUSWAP_test.log` or run-linked `verdacht.asc` has been recovered through the currently accessible loose-Library and repository-branch routes.

Status:
`PRE_V038_SELECTED_MEMBER_AGGREGATION_PRIORITIZED_NOT_QUALIFIED`.

### Missing DRA evidence

Still required for a defensible historical replay/admission:
1. exact pre-v0.38 source, binary or self-identifying producer log if recoverable;
2. exact run-linked suspect/selected-cell mask or equivalent semantics;
3. independent historical `lengte_p_250.asc`, `lengte_s_250.asc`, `lengte_t_250.asc`;
4. exact historical input hashes or evidence binding recovered rasters to the realized run.

Status:
`DIRECT_DRA_PRODUCER_ADMITTED = false`.

## Suspect/rest donor-cell workflow

Keep three concepts separate:
1. legacy pre-HRU `svat_donor` marker;
2. operational Piet R procedure assigning `hru_cluster_donor_svat`;
3. `hru_representative_svat`.

Piet's R procedure remains the operational suspect/rest target donor assignment currently accepted for reconstruction.

Do not silently merge this with the v0.35/v0.36 selected-member provenance question.

## Real-source Q4 and full production line

Still not closed:
- complete authoritative LHM server run tree;
- Q0-Q3 qualification on that tree;
- Q4 source collection and immutable bundle;
- downstream consumer smoke test;
- real-server Python post-processing golden regression;
- complete 10,242-run end-to-end production regression/admission.

These are now integration/production gates rather than basic workflow-discovery tasks.

## What is safe to say in project discussion

The project is **not stuck at the beginning**. The workflow, datamodel, 49-run oracle, key drainage-spacing semantics, post-processing architecture and most comparison infrastructure are recovered.

The remaining uncertainty is concentrated in:
- exact historical SWP template version;
- exact March-2026 DRA producer/source/input provenance;
- historical selected/suspect-cell semantics;
- three drainage length rasters;
- real-server end-to-end qualification.

This means modern production development can continue, but historical equivalence must remain explicitly bounded where provenance is missing.

## Recommended next work

### Highest-value recovery questions for colleagues/server

Ask whether any of the following still exist on the LHM/server/project storage:
- `exe\HRU2SWAP.exe` from the March-2026 run;
- `HRUSWAP_test.log` from that run;
- v0.35 or v0.36 `HRUlist2SWAP.f90` source snapshot/project directory;
- the exact `verdacht.asc` used in that run;
- `BasicData\grids\lengte_p_250.asc`;
- `BasicData\grids\lengte_s_250.asc`;
- `BasicData\grids\lengte_t_250.asc`;
- the exact historical `swap_wwl.swp`;
- a small complete authoritative LHM output period plus its historical post-processing outputs.

These are evidence requests, not requests to redesign the workflow.

### If historical artifacts are recovered

1. hash and persist them;
2. bind them explicitly to the historical run;
3. run diagnostic selected-member DRA replay;
4. run complete 49-run DRA regression;
5. run complete 49-run SWP regression;
6. classify only independently qualified differences as intentional.

### In parallel

Proceed with:
- Python server post-processing golden regression;
- declarative post-processing orchestration;
- real-source Q4 qualification;
- eventual 10,242-run end-to-end smoke/admission.

## Current priority order

1. recover exact historical producer/template/mask/length evidence from server/project storage;
2. perform small real-server Python post-processing golden regression;
3. complete selected-member provenance diagnostic if evidence permits;
4. close full 49-run DRA gate;
5. close full 49-run SWP gate;
6. qualify real-source Q4 bundle;
7. run 10,242-run end-to-end production smoke/admission.

No new admission is granted by this handoff.
