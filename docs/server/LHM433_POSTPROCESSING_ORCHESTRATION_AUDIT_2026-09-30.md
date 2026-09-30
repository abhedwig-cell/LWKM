# LHM 4.3.3 post-processing and source-transfer audit — 2026-09-30

## Scope

This note separates three things that had become mixed in the historical server workflow:

1. configured LHM source provenance;
2. scientific/post-processing derivation of diagnostic grids;
3. archival/cleanup of LHM output.

The control files remain the authority for configured LHM inputs. Historical batch files and executables are treated as implementation evidence, not as provenance authority.

## Raw artefact recovery status

Recovered as actual runtime bytes:

- `source (2).zip`, containing the historical Fortran sources;
- `exe.zip`, containing the executable/post-processing package.

Located in Project Files/Library but still blocked for raw-byte materialisation by the current Project backing-file authorization:

- `control_runs.zip`;
- `Tools(2).zip`;
- `Template.zip`;
- `Datamodel_10242.xlsx`;
- `SVAT_INFO(1).CSV`;
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`.

Copying those Project-backed files to a temporary Library folder succeeds at metadata level but does not remove the underlying raw-byte authorization restriction. This is therefore an access limitation, not evidence that the files are absent.

## Executable package inventory

The recovered `exe.zip` contains 27 entries. The scientific/post-processing executables that are demonstrably referenced by the supplied batches are:

| executable | observed role |
| --- | --- |
| `modflowidf2asc.exe` | aggregate MODFLOW daily IDF series over a requested date interval, optionally split positive/negative contributions |
| `gridcalc.exe` | grid algebra, quarter/year/season aggregation, climate averaging, diagnostic water-balance combinations |
| `grid_adjust.exe` | ground-level/head adjustment in the GVG workflow |
| external `C:\winrar\rar.exe` | archive old IDF series after processing |

`gridcalc_modflow.exe` is present in the package, but no use of it has yet been demonstrated in the supplied active batches. It must not be assigned a production role merely because it exists.

## Historical orchestration

### MetaSWAP

`do_idf2calc_year.bat` converts decade MetaSWAP IDFs into quarter, annual, summer and winter grids with `gridcalc.exe`.

`do_gridcalc_klimaat_ms_2011-2020.bat` then averages annual grids over 2011–2020 and applies the historical unit conversion. It also derives total sprinkling as `bdgPsgw + bdgPssw`.

### MODFLOW

Two historical routes coexist.

The long-period decade route uses `do_modflow_waterbalans*.bat` with `modflowidf2asc.exe` to create decade sums.

The 2011–2020 route in `do_modflow_waterbalans_2011-2020.bat` instead:
1. aggregates daily MODFLOW IDFs to quarterly grids;
2. combines quarters into annual, summer and winter grids;
3. optionally averages 2011–2020 and aggregates river/drain systems.

This distinction matters. A compact replacement in the Library currently has a step `03_modflow_extract_decade_grids.bat` followed by `04_modflow_make_climate_grids.bat`. Step 03 creates decade grids while step 04 expects annual grids. There is no demonstrated bridge between them. That compact chain is therefore **not admitted** as a faithful replacement yet.

### Derived water balance

`do_modflow_sumrivdrndec.bat` combines river/drainage terms, MetaSWAP terms and `bdgflf` into `bdgqmsw` and `bdgqlat`.

A historical defect is visible in the supplied script: the grid calculation that should create the combined river/drain result (`outf1`) is commented out, while a later active expression still consumes `outf1`. A modern implementation must not silently activate this calculation and call the result historical equivalence. It needs a separate defect-fix qualification against known outputs.

### GVG

The supplied `do_modflow_GVG.bat` constructs dates with `%mm%` although no assignment of `mm` is visible in the active context. A rewritten script in the Library replaces this by explicit 14 March, 28 March and 14 April dates. That is a plausible correction, but again it is a historical defect fix rather than a semantics-neutral refactor.

### Archival

`do_rar.bat` and `do_rar_flf.bat` only package old head/corrected-FLF IDFs by decade. They are operational cleanup and are not required to establish the LHM-to-LWKM source contract.

## Control-period chain

The available archival batches partition the long run as:

- 1970–1979;
- 1980–1989;
- 1990–1999;
- 2000–2009;
- 2010–2019;
- 2020–2022.

A loose file named `control_run_1970_1979.ini` is present. The names and ordering of the remaining controls are strongly suggested by the archive partition, but cannot be declared verified until `control_runs.zip` can be read as raw bytes. Do not promote the inferred six-control chain to repository authority yet.

## Source-bundle implementation

The repository now has a v2 portable source-bundle implementation with:

- an explicit resolved JSON collection plan;
- multiple control files per bundle;
- SHA-256 hashes for controls and payloads;
- content-addressed `objects/<sha256>` storage;
- deduplication of identical physical payloads referenced by several periods;
- optional embedded run-chain provenance;
- structural and hash verification;
- verify-before-unpack behavior;
- refusal to unpack into a non-empty snapshot directory;
- retained backwards verification support for v1 bundles.

CLI surface:

```text
python -m tools.lwkm_source_cli collect --plan <plan.json> --output <bundle.zip>
python -m tools.lwkm_source_cli verify <bundle.zip>
python -m tools.lwkm_source_cli inspect <bundle.zip>
python -m tools.lwkm_source_cli unpack <bundle.zip> --target <snapshot-dir>
```

Collection remains intentionally explicit. The tool does not crawl an LHM installation and infer dependencies.

## Qualification status

**QUALIFIED IMPLEMENTATION CANDIDATE, NOT SERVER-ADMITTED.**

Qualified locally with synthetic regression tests for:
- multi-control bundling;
- content deduplication;
- verification;
- invalid control references;
- immutable unpack target;
- CLI collect/verify/unpack round trip.

Still required for server admission:

1. raw access to the full control-file chain;
2. exact period/order binding;
3. producer-level dependency tracing to narrow the current generic run-output patterns;
4. one real LHM 4.3.3 bundle built and verified from the server;
5. consumer smoke test from the unpacked immutable snapshot.

## Consequence for the migration

The historical post-processing batches should not define the new transport boundary. The bundle should carry only the configured static/period inputs and the exact LHM run outputs needed by the downstream LWKM/SWAP producers. Diagnostic climate grids and archive RAR files belong downstream or outside the source bundle unless a producer dependency proves otherwise.
