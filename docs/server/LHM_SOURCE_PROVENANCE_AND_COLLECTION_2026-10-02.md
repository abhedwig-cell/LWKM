# LHM-server source provenance and collection procedure — 2026-10-02

## Purpose

This document defines the first production gate in the reconstructed LWKM workflow:

`LHM server -> immutable qualified source snapshot -> downstream LWKM processing`.

The purpose is to make explicit:

1. which files are considered source/basis files;
2. which files are only run-bound configuration or provenance evidence;
3. which files are derived and therefore must not become source authority;
4. how the authoritative server state is collected without changing it;
5. how the collected state is verified and frozen as an immutable ZIP bundle.

This procedure precedes all new Python post-processing, HRU generation and SWAP input generation.

## File-level qualification authority

Project-wide authority:
`docs/governance/LWKM_FILE_QUALIFICATION_POLICY_2026-10-02.md`.

The Q0-Q4 collection procedure freezes and proves the integrity of a source snapshot. It does not by itself make every contained file semantically production-admitted.

Each downstream-consumed file must also have sufficient file-level qualification for its intended use, including:
- SHA-256 identity;
- provenance binding;
- format qualification;
- semantic contract;
- downstream consumer;
- qualification evidence;
- regression qualification when required.

Therefore:
`Q4 BUNDLE QUALIFIED` does not imply `ALL MEMBERS PRODUCTION_ADMITTED`.

## Core provenance rule

A file is a **basis file** when:

- a downstream LWKM step consumes it directly; and
- it does not need to be reconstructed from another file inside the same qualified source snapshot.

A file is not promoted to basis authority merely because it happened to exist on the historical server.

Derived files remain derived even when they were historically produced by Fortran, batch, R or GridCalc.

Historical run inputs can be important provenance evidence without becoming modern scientific authority.

## Four provenance classes

### A. Authoritative LHM run output

Files emitted by the authoritative LHM/MODFLOW/MetaSWAP run and consumed by LWKM or its qualified post-processing.

Examples already visible in the reconstructed workflow include:

- MODFLOW head files for layer 1;
- `bdgflf` files;
- `bdgqlat` files;
- relevant river/drain budget or state products that are direct inputs to the admitted LWKM post-processing route.

Exact filenames, date coverage and formats must be inventoried from the actual server run tree. No assumed date range or filename variant is admitted until Q1 inventory.

### B. Authoritative static model/schematisation inputs

Static grids/tables that belong to the model state used by the run and are consumed directly by the LWKM/HRU/SWAP workflow.

The current recovered control file identifies at least the following candidate inputs. Their exact server paths and run binding still need Q0/Q1 confirmation:

- `header.asc`;
- `svat.asc`;
- `lgn250.asc`;
- `bodem.asc`;
- `soil2.asc`;
- `uopp.asc`;
- `beregen.asc`;
- `rootzone_m.asc`;
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`;
- `vcw_L1.idf`;
- `mdl_kd_l1.idf`;
- `bbc_afv.asc`;
- meteorological district/grid definitions;
- drainage conductance grids;
- drainage/infiltration-factor grids;
- drainage bottom-level grids;
- summer/winter level grids;
- `lengte_p_250.asc`;
- `lengte_s_250.asc`;
- `lengte_t_250.asc`.

The three length rasters are currently unresolved in the reconstructed evidence and are therefore high-priority server-recovery targets.

### C. LWKM run-bound inputs and configuration

These files are required to reproduce a particular historical or modern LWKM execution but are conceptually separate from raw LHM model output.

Examples include:

- HRU/SVAT membership tables;
- representative-SVAT tables;
- lookup tables such as BOFEK/soil/crop mappings;
- `qmodf_correct2.csv`;
- `verdacht.asc` or its exact run-bound equivalent;
- `control_LHM433_HRU_SWAP_10242.inp`;
- batch files that launch the producer.

These must be preserved with provenance, but their scientific authority is assessed separately.

In particular:
- `verdacht.asc` is a run-bound mask, not automatically a primary physical source grid;
- donor assignments, representative SVAT selection and suspect-cell handling must remain semantically distinct.

### D. Runtime/build provenance

Files that identify how the historical run was executed:

- `HRU2SWAP.exe`;
- `HRUSWAP_test.log`;
- source snapshots;
- compiler/project files;
- launch batch files;
- SWP templates;
- version files.

These are essential for historical reproducibility but are not themselves physical model input.

The March-2026 `HRU2SWAP.exe`, `HRUSWAP_test.log`, pre-v0.38 source snapshot and exact `swap_wwl.swp` are currently unresolved and should be explicitly searched on the server/project storage.

## Files that must not be treated as basis authority

Unless a later audit explicitly changes their status, do not classify as primary basis files:

- generated HRU directories;
- generated SWP files;
- generated DRA files;
- generated BBC files;
- generated MET files;
- post-processed yearly/seasonal/climate ASCII grids;
- temporary GridCalc products;
- filters that can be deterministically reconstructed from qualified source data;
- diagnostic files;
- regression reports;
- new Python outputs;
- ZIP timestamps.

The historical 49-run SWP/DRA/BBC/MET archive remains a **realized executable oracle**, not a raw LHM source bundle.

## Executable implementation

The server procedure is implemented by:

- `tools/server/lwkm_w01.py` — Q0-Q4 orchestration;
- `config/source/lhm-server-source-spec-v1.csv` — executable source inventory specification;
- `tools/lwkm_source_bundle.py` — existing tested low-level portable bundle format/verification;
- `docs/server/W01_LHM_SERVER_EXECUTION_GUIDE_2026-10-02.md` — exact server commands.

Q0 supports multiple explicitly named roots. The initial executable spec distinguishes:
- `RUN`: authoritative dynamic LHM/MODFLOW run output;
- `PROJECT`: run-bound BasicData/LWKM configuration/runtime tree.

These roots may be identical if the actual server layout warrants that, but they are recorded separately so provenance is not hidden behind one broad drive-level root.

The first real server session must stop after Q1 for review. Q2-Q4 are run only after the inventory and source specification have been reviewed.

## Step 1: identify the authoritative server run

Before copying anything, record one exact server/run identity.

Required Q0 metadata:

- server hostname;
- absolute source root;
- model/run name;
- LHM version if known;
- simulation period;
- source-tree last-modified context;
- owner/contact if relevant;
- whether the tree is a completed run or a working directory;
- whether any files may still be changing;
- known restart/continuation history;
- collection operator;
- collection timestamp in UTC;
- procedure version.

No files should be edited, renamed, regenerated or normalized in the source tree.

If the tree is still active, Q0 fails until a stable completed snapshot/root can be identified.

## Step 2: create a source-selection specification

Do not ZIP the whole server tree blindly.

Create a versioned source specification listing every file or filename pattern that the downstream pipeline is allowed to consume.

Recommended columns:

| Field | Meaning |
| --- | --- |
| provenance_class | A, B, C or D |
| required_by | downstream step consuming the file |
| source_path_or_pattern | path relative to the declared server root |
| required | YES/NO |
| temporal_scope | static, daily, monthly, period, etc. |
| expected_format | IDF, ASC, CSV, INP, EXE, LOG, etc. |
| notes | semantic role or qualification caveat |

The first Q1 inventory runs this specification against the server tree and records:

- every matched file;
- every missing required file;
- every ambiguous duplicate;
- every unexpected filename/date gap.

Q1 passes only when every required input has one explicitly resolved source identity or an explicit documented exception.

## Step 3: copy to a clean staging area

Create a staging directory outside the authoritative run tree.

Recommended layout:

```text
LWKM_LHM_SOURCE_<RUN_ID>/
  00_manifest/
  10_lhm_dynamic/
  20_lhm_static/
  30_lwkm_run_inputs/
  40_runtime_provenance/
```

Copy files byte-for-byte while preserving their relative identity.

Do not:
- convert IDF to ASC;
- recalculate climate means;
- edit control files;
- fix filenames;
- patch historical defects;
- change NODATA;
- normalize line endings;
- regenerate missing files.

A missing file remains missing and is reported as such.

## Step 4: generate the file manifest before ZIP creation

For every collected file record at least:

- provenance class;
- relative path in bundle;
- original full server path;
- file size in bytes;
- source last-write time in UTC;
- SHA-256;
- downstream consumer;
- qualification status.

Recommended manifest:
`00_manifest/files.csv`.

Also write:
`00_manifest/collection.json`

with:
- Q0 run metadata;
- source root;
- bundle ID;
- procedure version;
- number of files;
- total bytes;
- manifest SHA-256;
- known omissions/exceptions;
- collector hostname and timestamp.

Important: source filesystem timestamps are provenance clues only. Content identity is controlled by SHA-256.

## Step 5: create the immutable ZIP

Only after the staging manifest is complete create the archive.

Recommended name:

`LWKM_LHM_SOURCE_<RUN_ID>_Q4.zip`

The archive must contain the manifest inside the ZIP.

After ZIP creation compute:

- ZIP SHA-256;
- ZIP byte size;
- manifest SHA-256.

Record these outside the ZIP as well, for example:

`LWKM_LHM_SOURCE_<RUN_ID>_Q4.sha256`

The ZIP file's internal timestamps are not authority.

## Step 6: independent Q4 verification

Q4 is not granted merely because a ZIP was created.

Verification procedure:

1. extract the ZIP into a fresh empty directory;
2. read the embedded manifest;
3. recompute SHA-256 for every extracted file;
4. compare path, size and SHA-256 against the manifest;
5. compare file count;
6. confirm every required source-spec item is represented;
7. confirm no forbidden derived-output class was silently promoted into the source set;
8. compute and persist the final ZIP SHA-256.

Q4 passes only with:

`ZERO UNEXPLAINED FILE IDENTITY DIFFERENCES`.

Qualified state:

`LHM_SOURCE_Q4_IMMUTABLE_SNAPSHOT`.

From that point onward downstream LWKM work references the source snapshot by bundle ID + ZIP SHA-256 + manifest SHA-256, not by an informal server path.

## Proposed Q0-Q4 gate meaning

For the first workflow step use the following explicit gates:

### Q0 — run identity

One stable authoritative server root and run identity are declared.

### Q1 — source inventory

Every required source/spec item is resolved; missing/duplicate/date-gap findings are explicit.

### Q2 — staged byte identity

All selected files are copied without transformation and individually hashed.

### Q3 — archive construction

Manifest, metadata and files are packaged into the versioned ZIP; archive hash is recorded.

### Q4 — independent verification

Fresh extraction reproduces the manifest exactly and the bundle is admitted as immutable downstream source authority.

## Practical Windows/PowerShell collection pattern

The actual production script should be versioned in this repository, but the server-side sequence should follow this pattern.

### 1. Declare roots

Use explicit named roots rather than one implicit tree:

```text
RUN=<absolute authoritative LHM run root>
PROJECT=<absolute run-bound LWKM/BasicData project root>
```

The exact command syntax is maintained in:
`docs/server/W01_LHM_SERVER_EXECUTION_GUIDE_2026-10-02.md`.

### 2. Use a versioned file-selection list

Do not hand-select files in Explorer.

The selection specification should come from the repository and be archived with the bundle.

### 3. Hash source files while collecting

For each resolved source file capture at minimum:

```powershell
Get-FileHash -Algorithm SHA256 <file>
(Get-Item <file>).Length
(Get-Item <file>).LastWriteTimeUtc
```

### 4. Create ZIP only from staging

Do not ZIP directly from the live model directory because:
- the selected set is then harder to audit;
- provenance classes cannot be separated cleanly;
- unexpected temp/derived files can leak into the archive;
- the manifest cannot be frozen before packaging.

### 5. Verify from fresh extraction

Use a different verification directory and recompute every file hash.

The collection script must fail closed on:
- missing required file;
- duplicate unresolved candidate;
- changed file during collection;
- hash mismatch;
- unexpected geometry/format only when that property is part of the source specification;
- extraction mismatch.

## Large-run handling

If the complete dynamic LHM run is too large for one practical ZIP, splitting is allowed only by a preregistered deterministic rule, for example by period or product family.

Example:

```text
LWKM_LHM_SOURCE_<RUN_ID>_STATIC_Q4.zip
LWKM_LHM_SOURCE_<RUN_ID>_DYNAMIC_1971_1990_Q4.zip
LWKM_LHM_SOURCE_<RUN_ID>_DYNAMIC_1991_2010_Q4.zip
LWKM_LHM_SOURCE_<RUN_ID>_DYNAMIC_2011_2021_Q4.zip
```

Then create one parent index containing:
- child archive names;
- child SHA-256 values;
- period/product coverage;
- combined source-spec version.

Do not split ad hoc after collection merely to fit storage.

## Relationship to downstream workflow

Once Q4 is admitted:

```text
LHM server
    |
    | Q0-Q4 provenance collection
    v
immutable LHM source snapshot
    |
    +--> Python post-processing
    |       |
    |       v
    |    qualified derived grids
    |
    +--> SVAT/HRU reconstruction
            |
            v
         HRU context
            |
            +--> DRA/BBC/MET
            +--> SWP renderer
                    |
                    v
                  SWAP
```

Every later product must be traceable to:
- source bundle ID;
- source ZIP SHA-256;
- source manifest SHA-256;
- transformation code version;
- transformation configuration version.

## Immediate server questions

Before executing the first real collection, establish on the LHM server:

1. What is the exact completed run root that produced the current LWKM source state?
2. Which parts of `BasicData` belong to that run and which are shared mutable project data?
3. Where are the three length rasters?
4. Where is the exact historical `verdacht.asc`?
5. Is the March-2026 `HRU2SWAP.exe` still present?
6. Is `HRUSWAP_test.log` present?
7. Is there a v0.35/v0.36 source/project directory?
8. Is the exact historical `swap_wwl.swp` present?
9. Which LHM output period is best suited for the first small golden regression?
10. Are there any server-side generated files currently mixed into directories that we intend to call source authority?

## Current decision

The first formal step in the LWKM production workflow is now:

`AUTHORITATIVE LHM SERVER RUN -> Q0-Q4 SOURCE COLLECTION -> IMMUTABLE HASHED ZIP SNAPSHOT`.

No downstream file should be called a provenance-safe LWKM basis file until it has passed this collection gate or has a separately documented authority route.
