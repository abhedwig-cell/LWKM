# Storage, transfer and workspace architecture

Status: **DRAFT AUTHORITY**
Scope: logistical and provenance architecture for the complete LHM → SVAT → HRU → SWAP workflow.

## 1. Core principle

The workflow must be managed as **one end-to-end process**, even when computation and data handling take place on different systems.

The physical location of a calculation does not determine scientific authority.

For every step there must be:

- one authoritative input package;
- one versioned configuration/code state;
- one reproducible transformation;
- one explicit output package;
- one handoff/acceptance check before the next step.

Copies used for computation are working copies. They do not become authority merely because they are the most recent copy on a local or network disk.

## 2. Main environments

### A. NHI/LHM server

Role:
- upstream model calculation;
- production of agreed LHM export products.

The full LHM run remains outside the LWKM workflow, but the export step is inside the controlled chain.

Required output:
- `LHM_EXPORT` package;
- manifest;
- file checksums;
- LHM version/run identifier;
- producer scripts/configuration;
- unit, period and sign metadata.

The handoff is accepted only after the package has been verified in the LWKM environment.

### B. W: drive

Role:
- durable project storage;
- authoritative project documentation;
- accepted configuration and small/medium canonical data products;
- manifests and evidence;
- accepted interface packages where storage size permits.

The W: drive is **not required to hold all intermediate computational data**.

It must contain enough information to reproduce the workflow from preserved authoritative inputs.

### C. Leo workspace / large-data working storage

Role:
- large temporary/staging data;
- transfer and transformation of raster/grid products;
- construction of SVAT/HRU/SWAP inputs;
- other data-intensive preprocessing that is impractical on W:.

This is a computational workspace, not an uncontrolled parallel authority.

Every run on Leo must reference the authoritative input package by manifest/checksum, not by an ambiguous filename copied from another directory.

### D. Distributed SWAP compute environment

Role:
- execute large numbers of SWAP simulations.

This environment may be operationally external to the day-to-day LWKM workspace.

Required handoff out:
- immutable SWAP_INPUT package;
- run manifest;
- checksums;
- SWAP executable/version;
- run list.

Required handoff back:
- result package;
- completion/status table;
- checksums;
- logs;
- run identifier.

### E. Returned SWAP postprocessing

Current practice includes postprocessing returned SWAP output into compact CSV summaries for inspection.

This is part of the workflow even if the compute platform itself is initially treated as a black-box execution service.

The postprocessing script and the definition of the summary CSV must therefore be versioned and bound to the SWAP run manifest.

### F. GitHub repository

Repository:
`abhedwig-cell/LWKM`

Role:
- workflow specifications;
- source code;
- configuration;
- manifests/templates;
- QA rules;
- small evidence tables;
- provenance documentation.

Large model data do not need to live in Git.

## 3. Authority versus working copies

Every artifact is assigned one status.

### SOURCE_AUTHORITY
Irreplaceable or externally produced source input that must be preserved.

Examples:
- accepted LHM export;
- alternative Flevoland LHM export;
- immutable static source datasets where needed.

### CANONICAL_PRODUCT
Accepted product of a reproducible LWKM transformation.

Examples:
- accepted SVAT_QUALIFIED release;
- accepted HRU10242 schema/mapping;
- accepted SWAP input manifest.

These can often be regenerated, but a compact accepted release may still be archived for audit and convenience.

### WORKING_COPY
Temporary copy used during processing.

May be deleted after accepted downstream products and provenance exist.

### EVIDENCE
QA reports, comparison tables, exception registers and logs supporting admission.

Must be retained with the corresponding run.

## 4. Handoff contract

A step is not complete when somebody says a file was copied.

A handoff is complete only when:

1. source package/run is identified;
2. expected files are listed in a manifest;
3. transferred files exist;
4. checksums match;
5. schema/geometry/basic metadata pass validation;
6. receiving step records the exact manifest/run-id it consumed.

The next step may only read files referenced by that accepted manifest.

## 5. No copies-of-copies policy

Production scripts must not rely on filenames such as:

- `final.csv`;
- `final_new.csv`;
- `copy2`;
- a local directory that happens to contain the expected name.

Instead, a run configuration points to an explicit package/run identifier.

Example:

```text
runs/
  LHM43-1991_2020-EXPORT-001/
      manifest.yml
      data/...

  LWKM20-SVAT-QUAL-003/
      manifest.yml
      data/...

  LWKM20-HRU10242-001/
      manifest.yml
      data/...

  LWKM20-SWAPINPUT-HRU10242-004/
      manifest.yml
      data/...
```

A human-readable alias such as `current` may exist, but scripts must resolve it to a fixed run-id before execution and record that resolved id.

## 6. Suggested directory model

The exact drive letters/physical roots can differ by machine, but the logical structure should be identical.

```text
LWKM/
  authority/
    lhm-export/
    static/
    svat/
    hru/
    swap-input/
    swap-output/

  workspace/
    staging/
    scratch/
    tmp/

  runs/
    <run-id>/
      manifest.yml
      config/
      logs/
      evidence/
      outputs/

  software/
    scripts/
    executables/
    lookup/

  docs/
```

On W: only the durable subsets of this structure need to be stored.

On Leo the `workspace` and large `runs/<run-id>/outputs` areas can be much larger.

## 7. Reproducibility rule

Derived large files do not all need to be archived forever if:

- the authoritative input package is retained;
- the exact code/configuration is retained;
- the transformation is deterministic or sufficiently specified;
- required external executables are version-bound;
- a manifest lists the generated outputs;
- QA evidence for the accepted run is retained.

If any of these conditions is false, the supposedly reproducible product should be treated as an authority artifact and retained until reproducibility is proven.

## 8. End-to-end consistency checks

Because the workflow spans systems, QA must also test logistics/provenance.

Mandatory checks include:

- HRU derivation uses the same accepted SVAT_QUALIFIED run as SWAP input generation;
- representative-SVAT SWAP and HRU-SWAP both refer to the same SVAT/HRU authority;
- Flevoland-corrected state is identical at HRU and SWAP consumer boundaries;
- no downstream script reads an unmanifested local copy;
- distributed SWAP output corresponds exactly to the submitted SWAP_INPUT manifest;
- postprocessing CSV points back to the exact returned SWAP run.

## 9. Immediate reconstruction tasks

For the current HRU10242/SWAP chain, identify:

1. where the exact input SVAT table used by Piet resided;
2. its checksum/version;
3. whether it contained the Flevoland-corrected state;
4. whether it already contained outlier/replacement treatments;
5. which exact files HRUlist2SWAP consumed;
6. whether those files were the same accepted SVAT authority;
7. which SWAP input package was submitted to distributed compute;
8. which returned output package Leo postprocessing used;
9. which script produced the current SWAP summary CSV.

These nine bindings form the minimum current-chain logistics audit.

## 10. Practical policy

The aim is not to centralize every byte.

The aim is to centralize **authority**.

Large data may move between systems, but every move must preserve identity through:

**run-id + manifest + checksum + configuration + QA evidence**.
