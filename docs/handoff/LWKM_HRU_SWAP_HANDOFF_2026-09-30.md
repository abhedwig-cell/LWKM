# LWKM LHM->HRU->SWAP handoff — 2026-09-30

## Purpose

Authoritative handoff for continuation in a fresh chat. Repository is the working authority. Do not rely on the old long chat for operational state.

Work branch:
  work/lhm-hru-swap-workflow-v1

Before any write in a continuation:
1. fetch this branch again;
2. read this handoff;
3. read the referenced contracts/audits below;
4. search Project Files / Library for named uploads before asking the user to upload anything again.

## User intent and working principles

- Reconstruct and modernize LHM -> SVAT -> HRU -> SWAP input generation.
- Preserve scientific provenance and historical behavior before changing it.
- Do not silently clean up historical errors; first reproduce/classify them.
- Piet's HRU schema is authority for representative HRU choices.
- Existing server-side Fortran programs may remain Fortran. Rewrite only with a concrete benefit.
- Batch/orchestration may be replaced or wrapped.
- Martin's R SWP generation is flexible but too slow and has unwanted side effects. Replace with a typed direct renderer supporting only needed functionality.
- Selective regeneration is required: do not rebuild 10,242 HRUs when only a subset/dependency changed.
- NHI/LHM upstream run remains upstream responsibility. LWKM qualifies that the run is complete enough to consume, but does not own MODFLOW restart mechanics.

## HRU representative authority

Piet HRU schema:
  export_HRUschema_10242_copy.csv
configured historically as HRU2SVAT_REPR_CSV.

Authoritative concepts:
- representative_svat
- representative root depth rz_repr
- representative BFE bfe_repr
- representative bodem bodem_repr
- representative land use resolved through the schema-selected representative SVAT

Modern code must not recompute representative land use, soil/profile or root depth by member majority when schema authority exists.

Read:
- docs/lhm-hru-swap/P12-HRU-REPRESENTATIVE-AUTHORITY.md
- docs/lhm-hru-swap/P12-SCHEMA-FIRST-STATIC-MODEL.md
- tools/p12_hru_representation.py
- tools/p12_static_model.py

## Spatial support contract

Never use ambiguous 'area' in new code.

Distinct supports:
- MODFLOW cell = 250 x 250 m = 62,500 m2.
- active SVAT area = uopp; can be <62,500 m2.

Current rules:
- DRA conductance/resistance uses full MODFLOW-cell support, not uopp.
- MET RAIN/ETref HRU weighting uses uopp.
- BBC prescribed-flux aggregation uses selected MODFLOW-cell support.
- all-member vs selected-member populations must remain explicit.

Read:
- docs/lhm-hru-swap/P12-SPATIAL-SUPPORT-TYPES.md
- config/p12/spatial-support-v1.yml
- config/p12/accounting-support-v1.yml

## DRA

Current intended system order:
  pri, sec, ter, dra, glk

Core reconstruction implemented:
- DRARES = (62500 * N members) / sum(conductance), with legacy caps.
- INFRES uses conductance * infiltration factor.
- representative depths/levels are conductance-weighted.
- systems 4/5 historically have inf=0 in the reconstructed producer path, hence INFRES=100000 there unless executable provenance differs.
- all HRU members are intentionally included. This was explicitly confirmed by project owner.

Newly supplied missing raw rasters:
- ahn_f250_m.asc
- grensvlak_NHIWQ_v2_fill.asc
These were supplied in the old chat but local runtime was failing when full DRA realized gate was attempted.

dqsat:
- legacy computes dqsat using the provisional majority BFE, then later overwrites BFE with Piet bfe_repr without recomputing dqsat.
- affects Runs dqsat and DRA L=4*dqsat.
- classification: DEFECT_CONFIRMED_AUTHORITY_ORDERING.
- realized DRA L/4 is a useful independent oracle.

Nature:
- legacy computes isnatuur from provisional majority land use before Piet land-use override.
- affects DRA system 4 suppression.
- classification: DEFECT_CONFIRMED_AUTHORITY_ORDERING.

Read:
- tools/p12_dra_aggregate.py
- tests/test_p12_dra_aggregate.py
- docs/lhm-hru-swap/P12-DRA-REALIZED-GATE-STATUS.md
- docs/lhm-hru-swap/H-P12-STATIC04-DQSAT-ORDERING.md
- docs/lhm-hru-swap/H-P12-STATIC02-LANDUSE-ORDERING.md

## Static defects / resolved semantics

RDS:
- confirmed legacy control-flow defect: fallback evaluated inside member loop.
- but in current representative 10,242 path rds_maj is later overwritten by rz_repr/100.
- classification: DEFECT_CONFIRMED_CONTROL_FLOW_BUT_OVERRIDDEN_IN_CURRENT_REPR_MODE.
- do not port defective fallback into modern production.

Irrigation:
- threshold 0.37 is intentionally calibrated. Preserve.
- old comment saying 30% is stale documentation.
- current calibration is member-count fraction, not uopp. Do not change support without calibration evidence.

SWETR / is_nature:
- must derive from authoritative representative land use.
- legacy ordering defect confirmed.

soil2:
- means coarse sand/loam versus clay/peat class for crop mapping.
- it is deterministically lookup-derived from soil classification, not a fresh HRU decision.
- do not use legacy member-majority soil2 in modern production.

GWLI:
- SWAP initial groundwater level, approximately physically correct rather than a sensitive representative parameter.
- historical source is MODFLOW initial/stationary head relative to mean ground level:
  GWLI=min(0,round((hh_avg-glk_avg)*100)).
- preserve simple MODFLOW-derived initialization unless evidence supports simplification.
- status SEMANTICS_RESOLVED_INITIALIZATION_LOW_SENSITIVITY.

SWALLO:
- source 'infil' is riv_infil = LHM_uitvoer/filter/Riv_infiltratie_1991-2020.asc.
- treat as independent long-term river-infiltration indicator, not soil property.
- historical rule:
  system>3 OR INFRES>20000 OR indicator<10 -> SWALLO=3, else 1.
- exact unit/provenance of threshold 10 remains documentation-open but does not block compatibility.

Read:
- docs/lhm-hru-swap/H-P12-STATIC01-AGGREGATION-AUDIT.md
- docs/lhm-hru-swap/H-P12-STATIC03-SOIL2-AUTHORITY.md
- docs/lhm-hru-swap/P12-GWLI-INITIALIZATION-CONTRACT.md
- docs/lhm-hru-swap/P12-SWALLO-RIVER-INFILTRATION.md
- tools/p12_landuse_flags.py
- tools/p12_swallo.py

## Soil lookup

Project owner remembers making corrections to derive the correct BOFEK from the 370 soil units.

Do NOT use Bodem370_2_bofek2020.csv blindly as authority.

Earlier reconstruction from realized SVAT_INFO found deterministic:
  bodem370 -> BOFEK79 -> PAWN21 -> grondsoort4 -> grondsoort2

Known realized BOFEK corrections relative to old reference:
- 78: 40 vs 39
- 79: 39 vs 40
- 81: 39 vs 44
- 82: 44 vs 39
- 94: 31 vs 28
- 95: 28 vs 31
- 147: 46 vs 41
- 148: 41 vs 46
- 170: 44 vs 39
- 171: 39 vs 44

Five codes were unobserved in realized population:
  14, 142, 143, 197, 198

Raw upload supplied:
  SVAT_INFO(1).CSV

Runtime failed while trying to generate the complete 370-row table. Retry in fresh chat/runtime. Do not hand-fill 365 rows.

Read:
- docs/lhm-hru-swap/P12-BODEM370-BOFEK-LOOKUP-AUTHORITY.md
- docs/lhm-hru-swap/P12-BODEM370-LOOKUP-REGENERATION-GATE.md
- config/p12/bodem370_bofek_known_corrections.csv
- tools/build_bodem370_lookup.py
- tests/test_bodem370_lookup.py

## MET

Established:
- meteo district is all-member category majority.
- WET is rain duration: must be absent/zero-compatible when rain=0 and >0 when rain>0 according to historical compatibility policy.
- district behavior qualified on 49 realized runs.
- WET behavior qualified over 17,885 rows.
- RAIN/ETref aggregation uses uopp, not 62,500 m2 cell area.
- 250 m cells determine location in 1 km meteo pixels; uopp determines HRU weight.

Read:
- docs/lhm-hru-swap/P12-MET-SPARSE-AGGREGATION.md
- tools/p12_meteo_weights.py

## BBC

BBC/QBOT2 producer was reconstructed earlier in this workstream.
Keep membership/executable provenance separate from static HRU authority.
c1 is vertical resistance in days between phreatic layer and underlying aquifer.
In LHM control provenance it maps to VCW_l1.idf.

Read relevant BBC documents already present under docs/lhm-hru-swap and config/p12 before modifying.

## 49-run integrated regression oracle

Do not compare only outputs for which legacy and corrected hypotheses are identical.

For each observable classify discriminating vs non-discriminating:
- SWETR: legacy majority land use vs Piet representative land use.
- DRA4 nature: same, excluding cases already shut by DRARES>20000.
- soil2: legacy member majority vs canonical lookup from representative soil.
- dqsat: legacy majority-BFE population vs representative-soil semantics; realized L/4 is oracle.
- RDS expected non-discriminating in current repr mode.
- DRA aggregation numeric gate.
- BBC/QBOT2.
- GWLI historical characterization.
- SWALLO historical compatibility.

Read:
- docs/lhm-hru-swap/P12-49RUN-INTEGRATED-REGRESSION-ORACLE.md
- config/p12/regression-oracle-v1.yml

## Runs / direct SWP renderer

Legacy Fortran writes a 37-field Runs CSV for Martin's R/Datamodel procedure rather than direct SWP.

Typed replacement implemented:
- tools/p12_run_record.py
- docs/lhm-hru-swap/P12-RUNS-REPLACEMENT-CONTRACT.md

Renderer principle:
- renderer formats typed values only;
- it must not redo HRU majority decisions;
- BBC/DRA/MET remain separately produced referenced files;
- unknown template fields are fatal;
- no automatic generation of unrelated inputs;
- selective regeneration based on dependency hashes.

Read:
- docs/lhm-hru-swap/P12-DIRECT-RENDERER-ADMISSION.md

Important uploads for renderer:
- Tools(2).zip
- Datamodel_10242.xlsx
- Template.zip
- realized run directories supplied earlier, including .dra files

These raw uploads could not be unpacked because the local runtime/container repeatedly failed. In a fresh chat FIRST search Project Files / conversation uploads / Library for them. Do not ask user to upload again until retrieval/materialization has genuinely failed.

The report Rapport_Koppeling_SWAP4_en_MODFLOW6_nieuwe_template_v3.docx also contains a standard swap.swp.template description, but use actual Template/R tooling as historical oracle when available.

## NHI/LHM server logistics

User-approved responsibility split:
- existing Fortran programs on NHI server remain Fortran unless a rewrite is demonstrably better;
- batch orchestration may be modernized;
- LHM/MODFLOW run and restart mechanics are upstream responsibility;
- LWKM checks source-run completeness before accepting it.

The LHM run control file is primary configured-source provenance.
Example uploaded and indexed:
  control_run_1970_1979.ini

Important facts from it:
- model root e:\LHM_4.3.3
- model data under Data\2_Model_Input
- starting heads HEAD_STEADY-STATE_l*.idf
- c1 = VCW_l1.idf
- explicit DRN/RIV conductances, stages, bottoms, infiltration factors
- MetaSWAP uopp, ground, lgn, soil, rootzone, meteo grids
- annual meteorological source families
- executable references
- restart configuration

Source bundle concept:
- preserve original control files;
- resolve aliases;
- select only LWKM dependencies;
- include required run outputs;
- SHA-256 every payload;
- deduplicate identical files;
- create portable ZIP with manifest;
- verify before use;
- unpack into immutable LWKM source snapshot.

LWKM does NOT own MODFLOW restart mechanics.
Qualification levels:
- Q0 CONFIGURED
- Q1 PERIOD_COMPLETE
- Q2 OUTPUT_COMPLETE
- Q3 EXECUTION_EVIDENCE
- Q4 LWKM_SOURCE_QUALIFIED

Read:
- docs/server/NHI-LHM-PROVENANCE-CONTRACT.md
- docs/server/LHM-MULTIPERIOD-SOURCE-BUNDLE.md
- docs/server/NHI-TO-LWKM-TRANSFER-CONTRACT.md
- docs/server/LHM-UPSTREAM-RUN-QUALIFICATION.md
- docs/server/SERVER-LOGISTICS-STATUS.md
- config/server/lhm433-lwkm-transfer-profile.yml
- tools/lhm_control_provenance.py
- tools/lhm_run_chain_provenance.py
- tools/lwkm_source_bundle.py
- tools/lwkm_source_cli.py

## Server/logistics uploads not yet fully inspected because runtime failed

Raw uploads:
- exe.zip
- control_runs.zip

Loose batch files supplied:
- do_modflow_waterbalans_flfcorr_dec.bat
- do_modflow_waterbalans_lat_dec.bat
- do_rar.bat
- do_rar_flf.bat
- do_gridcalc_klimaat.bat
- do_idf2calc_year.bat
- do_modflow_GVG.bat
- do_modflow_sumrivdrndec.bat
- do_modflow_waterbalans.bat
- do_modflow_waterbalans_flf_dec.bat

User believes these are probably the relevant batch files.

Fresh chat must first retrieve/read these existing Project/conversation uploads. Do not ask for re-upload merely because old runtime failed.

## Other important earlier uploads / project files

Search existing Project Files / Library before requesting:
- LWKM_workflow_no_asc.zip
- source (2).zip (Fortran sources)
- control_mkHRU.inp
- control_LHM433_HRU_SWAP_10242.inp
- do_mkHRU_INFO.bat
- do_HRU2SWAP_10242.bat
- run directories / realized .dra files
- raw grids and drainage archives supplied during this workstream
- filter_lwkm.asc and related workflow material

The Fortran sources have already been used extensively and should be recoverable from project/library context.

## Current blockers caused by old chat runtime, not by user data

The local Python/container runtime repeatedly returned a system/client error, preventing:
- unpacking ZIP uploads;
- reading loose raw batch files through the mounted sandbox;
- generating the full canonical 370-row soil lookup from raw SVAT_INFO;
- running full raw-grid 49-run DRA regression.

Do not assume these failures persist in a new chat. Retry there.

## Immediate continuation priorities

Work in large autonomous blocks.

Priority A — recover raw artifacts in fresh runtime
1. inspect control_runs.zip;
2. inspect exe.zip and loose .bat files;
3. inspect Tools(2).zip, Template.zip and Datamodel_10242.xlsx;
4. retry raw SVAT_INFO lookup generation;
5. retry newly supplied DRA source rasters.

Priority B — close server logistics
1. derive exact multi-period control/run chain;
2. map current batch -> executable -> input -> output orchestration;
3. identify which batch logic is required, obsolete, or replaceable;
4. finish server-side collect/verify bundle command;
5. define exact run-output subset needed by LWKM.

Priority C — direct SWP renderer
1. inventory actual R/template tokens and side effects;
2. map them to typed P12RunRecord / database lookup / producer references;
3. implement minimal direct renderer;
4. reproduce one realized run;
5. expand to 49-run regression;
6. retire R from production path only after no unexplained differences.

Priority D — numerical/authority closure
1. generate canonical 370-row soil lookup;
2. quantify STATIC02/03/04 impact over all 10,242 HRUs when raw data available;
3. complete DRA 49-run numeric gate;
4. preserve intentional corrected differences explicitly.

## Working rule for fresh chat

Repository and Project Files are authority. Work autonomously in large blocks. Ask the user only for a genuine missing scientific decision or a file that has first been searched for and cannot be recovered from Project/Library/conversation uploads.
