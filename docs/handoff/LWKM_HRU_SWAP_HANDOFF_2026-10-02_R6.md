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

## Project-wide file qualification rule

Authority:
`docs/governance/LWKM_FILE_QUALIFICATION_POLICY_2026-10-02.md`

Project invariant:

`EVERY CONSUMED FILE MUST BE INDIVIDUALLY QUALIFIED`.

Presence on the server, in an archive, in a historical run or in an earlier workflow is not sufficient.

Every consumed file must ultimately have a stable logical identity, SHA-256, provenance, semantic role, downstream consumer and qualification evidence. Derived files must additionally bind their qualified parents, transformation code/configuration and output hash.

A Q4 ZIP qualifies collection integrity, not automatically semantic production suitability of every member. File-level qualification remains required throughout the full LHM -> SVAT -> HRU -> SWAP chain.

Target end state:

`100% OF CONSUMED FILE IDENTITIES QUALIFIED`

and

`ZERO UNTRACED PRODUCTION INPUTS`.

## Stepwise production-chain qualification

Authority:
`docs/governance/LWKM_PRODUCTION_CHAIN_QUALIFICATION_PROTOCOL_2026-10-02.md`

Machine-readable chain:
`config/governance/lwkm-production-chain-v1.yml`

From this point onward, the reconstructed workflow is closed from left to right through explicit steps W00-W14. Each step has:
- qualified input authority;
- an explicit transformation contract;
- an output contract;
- qualification tests;
- a persisted admission gate.

No step is considered complete because code or files merely exist. It is complete only when its evidence supports the defined admission state.

Current execution order starts at W01 on the real LHM server and then proceeds through postprocessing, SVAT, donor assignment, HRU construction, context assembly, DRA/BBC/MET, SWP rendering, package assembly, 49-run integrated regression, 10,242-run build and final end-to-end admission.

## W01 authority correction — 2026-10-05

Project-owner authority now fixes the first provenance boundary:

- LHM output authority is the Deltares-collected tree
  `G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`;
- LHM input/config authority is the set of project-owner supplied LHM `.ini` control files;
- reconstructing which underlying period-specific `run_*` directories were used is not a W01 admission prerequisite;
- HRU/SWAP runtime material is not expected on the NHI server and belongs to downstream provenance gates.

Read:
`docs/server/W01_LHM_AUTHORITY_SPLIT_2026-10-05.md`
and:
`config/source/w01-lhm-authority-v1.yml`.

W01 now proceeds by inventorying/qualifying downstream-used files from the authoritative total-results tree and by parsing/qualifying the INI-declared input/config graph.

## First formal workflow gate: LHM server source provenance

The workflow now starts with an explicit provenance freeze on the authoritative LHM server before any post-processing or HRU reconstruction.

Authority:
`docs/server/LHM_SOURCE_PROVENANCE_AND_COLLECTION_2026-10-02.md`

Machine-readable draft source specification:
`config/source/lhm-server-source-spec-v1.yml`

Required sequence:

`authoritative LHM server run -> Q0 run identity -> Q1 source inventory -> Q2 byte-identical staging + per-file SHA-256 -> Q3 versioned ZIP -> Q4 fresh-extraction verification -> immutable source snapshot`.

After Q4, downstream work must identify the source bundle by ZIP SHA-256 and manifest SHA-256 rather than by an informal server path.

The provenance model distinguishes:
- A: authoritative dynamic LHM run outputs;
- B: authoritative static model/schematisation inputs;
- C: LWKM run-bound configuration and masks;
- D: runtime/build provenance.

Generated HRU/SWP/DRA/BBC/MET and other post-processed products are not raw source authority.

The exact server run root and all source-spec candidates still require Q0/Q1 confirmation on the real server. In particular the historical length rasters, suspect mask, March-2026 producer binary/log and exact SWP template remain high-priority recovery targets.

## W01-O output inventory result — 2026-10-05

The Deltares-collected output authority has now been inventoried from metadata supplied from the real NHI server.

Authority root:
`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`.

Observed:
- 399,184 files;
- approximately 2.87 TB;
- `modflow`: 287,403 files;
- `metaswap`: 42,206 files;
- `postprocessing`: 69,575 files.

Current classification:
- raw `modflow` and `metaswap` are primary W01-O source candidates;
- `postprocessing` is derived/historical regression-oracle material unless a specific downstream contract says otherwise.

Important period structure:
- core MetaSWAP output and MODFLOW head/FLF extend through 2024;
- historical `bdgriv` and `bdgdrn` extend through 2022;
- 2023-2024 introduces changed/partitioned MODFLOW output representation;
- `bdgqmsw` and `bdgqlat` are observed as derived postprocessing products, not raw MetaSWAP subfolders.

Read:
`docs/server/W01_OUTPUT_AUTHORITY_INVENTORY_RESULT_2026-10-05.md`
and:
`config/source/w01-output-consumer-candidates-v1.yml`.

Do not hash or freeze the full 2.87 TB blindly. First close the exact consumer-bound source set and FLF ownership, then hash every consumed source file.

## W02 layer-1 RIV/DRN production authority — 2026-10-05

Project owner clarified that the historical RIV/DRN output contains more interaction than was previously carried through and that **all interaction in MODFLOW layer 1 must be included**.

The supplied LHM433 control INI confirms:
- RIV systems 1, 2, 3 and 4 are in layer 1;
- RIV systems 5 and 6 are in layer 2;
- DRN systems 1, 2 and 3 are in layer 1.

Modern W02 contract:
- include all RIV 1-4 layer-1 interaction;
- include all DRN 1-3 layer-1 interaction;
- keep RIV 5-6 as separate layer-2 provenance and do not silently mix them into a layer-1 net term.

Authority:
`docs/server/W02_LAYER1_SURFACE_WATER_INTERACTION_CONTRACT_2026-10-05.md`.

The current reconstructed all-RIV-system net sum is therefore not production-authoritative for a layer-1 interaction product.

`tools/lhm_postprocess.py` now has a strict helper that requires exactly RIV 1-4 and DRN 1-3 and rejects missing/extra systems. Unit tests cover complete membership, missing system 4 and accidental layer-2 RIV inclusion.

The revised 1970-2022 first source tranche is:
- 197,118 files;
- 1,142,039,024,280 bytes;
- approximately 1.142 TB;
assuming one selected FLF route and the current 12 MetaSWAP core families.

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

## DRA physical-system correction — 2026-10-06

Project authority corrects the five-system physical-source assumption.

The layer-1 physical drainage/surface-water system is now seven components:
- H1 main surface water;
- primary;
- secondary;
- tertiary;
- MVG/surface ditches;
- pipe drainage;
- OLF/overland flow.

The active HRUlist2SWAP code currently uses only five physical families (`pri/sec/ter/dra/glk`) and therefore omits H1 and MVG from resistance/depth derivation despite its own v0.21 history stating that hoofdwaterlopen and greppels were included.

SWAP exposes at most five drainage levels. The modern architecture is therefore:

`7 physical LHM systems -> full HRU aggregation -> explicit hydraulic compression -> <=5 SWAP levels`.

Do not hard-code a global pair deletion or merge.

Authority:
`docs/lhm-hru-swap/P12-DRA-SEVEN-TO-FIVE-LEVEL-DESIGN-2026-10-06.md`.

Machine-readable source model:
`config/p12/dra-physical-systems-v2.yml`.

Diagnostic compressor:
`tools/dra_level_compression.py`.

Synthetic execution passed the invariants:
- seven active sources reduced to five;
- pipe remained distinct;
- source lineage preserved exactly;
- drainage conductance conserved;
- infiltration conductance conserved.

Evidence:
`docs/evidence/2026-10-06/dra-seven-to-five-compression-diagnostic.json`.

This is not production admission. Real H1/MVG source files, L semantics, final SWAP ordering and 10,242-HRU diagnostics remain open.

## H1/MVG real-server Q4 recovery — 2026-10-07

The H1/MVG source bundle required by the seven-physical-system DRA redesign has passed a real-server Q4 collection and fresh-extraction verification.

Bundle identity:
- ZIP SHA-256: `3c27cb509dd6d60f5ae8b434fd1ba0f4aca10d81a1b1815b077c5b52a818abfa`;
- manifest SHA-256: `216af5086a83109abfcaa74b19c92535c354a79008ec958e0b7c0eb40fc32ebb`;
- 681 payload files;
- 4,249,475,616 payload bytes;
- zero unexplained file-identity differences.

H1 dynamic stage:
- 676 `peilh_*.idf` files;
- filename date range 1969-12-01 through 2026-03-01;
- 676 equals the inclusive calendar-month count for that range, strongly indicating gap-free monthly coverage;
- exact per-file sequence and hashes still need persistence from `files.csv`.

This closes the H1/MVG **source recovery** blocker. It does not yet grant semantic production admission. Remaining file-level work:
1. persist the individual member hashes from `files.csv`;
2. confirm exact monthly sequence with zero duplicates/gaps;
3. validate IDF geometry/NODATA/units;
4. wire H1 and MVG into the seven-system HRU aggregation;
5. run the 10,242-HRU compression diagnostic.

Evidence:
`docs/evidence/2026-10-07/h1-mvg-q4-summary.json`.

## H1/MVG file-level qualification — 2026-10-07

The uploaded H1/MVG Q4 ZIP has now been independently re-hashed in full:
- 681/681 payload files match the embedded manifest;
- 4,249,475,616/4,249,475,616 bytes accounted for;
- zero missing files;
- zero size/hash mismatches.

All 681 IDFs share the expected 1200 x 1300, 250 m geometry and national extent.

The H1 stage sequence is exactly gap-free monthly:
- 676 unique files;
- 1969-12-01 through 2026-03-01;
- zero missing months;
- zero duplicates.

MVG conductance and bottom/stage supports match exactly on 66,280 cells.

H1 has a small set of source-support exceptions that remain semantically open:
- 296 H1 conductance cells lack an explicit infiltration factor;
- one H1 conductance cell lacks a bottom and lacks stage for 2005-01 through 2021-12;
- April 2022 H1 stage is absent at 15 conductance cells;
- one H1 cell has stage below bottom in 436 monthly files.

The major bottom/stage anomaly coordinate pairs were not found in the indexed `svat_info_lwkm_new.csv` selected-population text search. Treat this only as a useful negative indication, not yet a complete population-intersection proof.

Evidence:
`docs/evidence/2026-10-07/h1-mvg-file-semantic-audit.json`.

H1/MVG source recovery and byte identity are closed. H1 exception semantics/population intersection remain open before seven-system DRA production admission.

## Seven-system DRA implementation progress — 2026-10-07

W07 is no longer generically blocked by unknown DRA source provenance.

Modern corrected production architecture is implemented through the diagnostic stage:

`7 physical systems -> all-member HRU aggregation -> hydraulic compression if >5 active -> explicit SWAP level repair/rendering`.

Implemented safeguards:
- physical-system identity is explicit, not encoded in SWAP level number;
- pipe/open-channel semantics are explicit;
- infiltration capability is explicit;
- weak but positive physical conductance is preserved until after compression;
- raw physical conductance and SWAP resistance are separate internal quantities;
- representative-SVAT dqsat gives the common modern L = 4*dqsat and is preserved through merges;
- H1 monthly level dynamics are preserved through compression and explicit DATOWL/LEVEL rendering;
- H1 monthly rasters are streamed once for the whole 10,242-HRU diagnostic rather than once per HRU;
- positive-conductance members with missing hydraulic attributes fail closed.

The full 10,242-HRU population diagnostic runner is:
`tools/diagnose_dra_10242.py`.

It expects:
- `export_svat_HRU_NRU_10242.csv`;
- a SVAT_INFO-style coordinate table;
- representative-dqsat authority;
- the Q4 H1/MVG ZIP;
- the Q4 remaining-five-source ZIP.

The current membership file has been recovered in Library at:
`/LWKM/export_svat_HRU_NRU_10242.csv`.

The remaining P/S/T/PIPE/OLF + AHN Q4 collector is:
`tools/server/lwkm_collect_dra_remaining.ps1`.

W07 status is now:
`MODERN_SEVEN_SYSTEM_IMPLEMENTED_SOURCE_Q4_PARTIAL`.

Admission remains false until the remaining source bundle is Q4-qualified and the 10,242-HRU diagnostic passes.

## DRA level ordering and package-index guard — 2026-10-07

SWAP 4.3.1 source authority has now been inspected through both the ordinary
DRAMET=3 flux path and DIVDRA vertical-distribution path.

Qualified W07 result:
- ordinary DRAMET=3 exchange is calculated per level and summed;
- DIVDRA constructs its own active-system sequence from `FDisInf * Lspacing`;
- LWKM writes `SWINTFL=0`, so the special last-level interflow semantic is inactive;
- modern serialized ordering is deterministic (depth, medium, source lineage);
- equal compression costs are tie-broken canonically by source lineage, independent of caller order.

Level number remains potentially semantic only for rapid macropore drainage
when `SWMACRO=1 && SWDRRAP=1`, because SWAP then uses
`NUMLEVRAPDRA`.

That question is moved to W10/W11. `tools/dra_package_guard.py` resolves
`NUMLEVRAPDRA` from post-compression source lineage and fails closed if an
old/stale numeric level cannot be reconciled.

Authority:
`docs/lhm-hru-swap/P12-DRA-LEVEL-ORDERING-RESOLUTION-2026-10-07.md`.

The 10,242-HRU W07 diagnostic is therefore no longer blocked by generic level
ordering.

## DRA 10,242 diagnostic input binding — 2026-10-07

The population diagnostic now has two provenance-correct representative-dqsat routes:

1. preferred recomputation from `export_svat_HRU_NRU_10242.csv` +
   `export_HRUschema_10242_copy.csv` + `grensvlak_NHIWQ_v2_fill.asc`;
2. STATIC04 qualified replay route using persisted
   `static04_dqsat_full_10242.csv`.

The loose schema-copy file is not currently recovered as a standalone Library
file, so the replay route can be used immediately without weakening STATIC04
authority. The recomputation route remains implemented for later independent
replay.

Machine-readable binding:
`config/p12/dra-10242-diagnostic-inputs-v1.yml`.

The diagnostic fails closed unless it sees exactly 427,656 membership rows,
10,242 HRUs, 10,242 representative-dqsat values and identical HRU domains.

It also compares P/S/T current-HRU bottom definitions against the actual LHM
package semantics; for T the LHM INI binds the river bottom to
`PEIL_T1Z/W_250.IDF`.

## W07 seven-system population preflight — 2026-10-07

The modern DRA route now has two population diagnostics.

1. `tools/diagnose_dra_activity_10242.py`
   - conductance-only;
   - requires no historical `BODH_*1J` bottoms;
   - counts active H1/P/S/T/MVG/PIPE/OLF systems for every HRU;
   - reports the 0..7 active-system distribution;
   - reports how many HRUs actually require >5 -> 5 compression;
   - compares the historical five-system activity population with the modern seven-system population.

2. `tools/diagnose_dra_10242.py`
   - full hydraulic compression diagnostic;
   - additionally requires qualified bottom/depth authority;
   - reports merge pairs, costs, dynamic H1 involvement, conductance conservation and bottom-authority comparisons.

The activity preflight is deliberately separated from bottom-authority admission so the factual frequency of 6/7 active physical systems can be established independently.

The remaining real-server source collector now treats historical `BODH_P1J/S1J/T1J` as optional evidence, not as required NHI/LHM inputs. This matches the project-owner authority that HRU/SWAP runtime/material is not an NHI-server W01 requirement.

Execution guide:
`docs/server/W07_DRA_REMAINING_Q4_EXECUTION_GUIDE_2026-10-07.md`.

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
