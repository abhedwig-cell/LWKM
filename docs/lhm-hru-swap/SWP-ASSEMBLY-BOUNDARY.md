# Historical SWP assembly boundary

Status:
**PRODUCER BOUNDARY AND TOP-LEVEL R SIDE EFFECTS RECOVERED; CURRENT TEMPLATE SERIALIZATION STILL BLOCKED**

## Historical producer boundary

HRUlist2SWAP v0.38 does not write the final `.swp` itself. It writes the run-level scientific/identifying fields plus separately generated BBC/DRA/MET assets for the downstream SWAPtools/Datamodel procedure.

The historical handoff therefore has two distinct layers:

1. HRUlist2SWAP decides/serializes the typed run record and produces auxiliary BBC/DRA/MET content;
2. SWAPtools joins that record to the Datamodel/domain tables and serializes a runnable SWAP case.

The modern workflow preserves this separation.

## Datamodel recovery

The earlier statement that the Datamodel had not been recovered is obsolete.

Raw-readable historical archive:
- `Datamodel_9830.zip`
- SHA-256 `7eed8c4e609c490efb8eb7cff998e537cf3530eb742709d44a05f2c36271b2f7`

Recovered from it:
- `Datamodel_10242.sqlite`
- historical `Datamodel_10242.xlsx`
- `SVAT_Waterbalans.xlsx`
- `swap_tools.log`
- `HRUSWAP_dra.log`

The recovered current-shaped SQLite is sufficient to qualify the datamodel-to-render-context layer across all 10,242 Runs. See:
- `P12-DIRECT-RENDERER-R2-CONTEXT-QUALIFICATION.md`;
- `DATAMODEL-TO-SWP-CONTRACT.md`.

## Top-level SWAPtools execution contract

The raw `swap_tools.log` from the historical archive has SHA-256:
`e691dfd5984c9ee4c5c3ed5a8e658fec9b79ece00b8159e516565db11549752c`.

It records the executed top-level R procedure.

The control file supplies:
- SQL database path;
- optional source XLS for database creation;
- run directory;
- requested RUNID selection;
- SWAP executable;
- SWP template;
- optional DRA/BBC/IRG templates;
- crop, meteorology, atmosphere, initial-condition, drainage, BBC and irrigation directories;
- CREATE / RUN / ZIP switches.

For every selected run the main process:

1. builds
   `<DIRRUN>/run_<zero-padded-run-id>/swap.swp`;
2. when CREATE is enabled, calls `create_SWAP(...)`;
3. when RUN is enabled, calls `run_SWAP(...)`;
4. when ZIP is enabled, archives selected outputs with `zip_SWAP(...)`.

The observed `create_SWAP` call receives:
- `file_swp`;
- `file_sql`;
- `run_id`;
- `tmplt_swp`;
- `dir_met`;
- `dir_atm`;
- `dir_ini`;
- `dir_crp`;
- `dir_dra`;
- `dir_bbc`;
- `dir_irg`;
- optional DRA/BBC/IRG templates.

This proves that the historical R layer is not just a pure SWP text-substitution call. It owns orchestration around input creation, execution, ZIP lifecycle and optional post-processing.

## Modern replacement boundary

The direct renderer must replace only the **input-creation/serialization** part of `create_SWAP`.

It must not silently absorb these unrelated SWAPtools side effects:
- executing SWAP;
- ZIP/extract lifecycle;
- post-processing plots;
- deleting extracted run directories;
- regeneration of BBC/DRA/MET scientific content.

Those remain separate explicit operations.

The modern rendering inputs are:
- typed run record;
- soil/profile/hydraulic/texture domain rows;
- crop/rotation rows;
- explicit config;
- references to already-produced BBC/DRA/MET assets.

Unknown template fields remain fatal.

## Historical DRA log limitation

The recovered `HRUSWAP_dra.log` has SHA-256:
`cc46c45b8a1dd70329090cd129ca6335bac98cc98d72474d7b395aaa9e255c76`.

Its own header identifies:
`HRUlist2SWAP version 0.22 aug2025`.

Current production authority is the later v0.38 line. The v0.22 log is therefore:
**HISTORICAL EXECUTION TRACE ONLY**.

It may be used to recover historical file dependencies or debug chronology, but not as a numerical oracle for v0.38 drainage behavior.

## Remaining serialization blocker

The current `Template.zip` is located in Project/Library but its backing bytes are still not authorized for raw materialization.

A historical template/mapping oracle has been inspected earlier, but it is not safe as current production template authority because, among other differences, it hard-codes SWETR=0 while 3,080 current Runs require SWETR=1.

Therefore the remaining direct-renderer boundary is narrow:

1. recover current template bytes, or admit an explicitly versioned canonical replacement;
2. render run 2000;
3. pass the semantic run-2000 oracle;
4. expand to the 49-run regression;
5. keep R/SWAPtools only as regression/orchestration reference, not production serialization dependency.

The datamodel and scientific context are no longer the blocker.
