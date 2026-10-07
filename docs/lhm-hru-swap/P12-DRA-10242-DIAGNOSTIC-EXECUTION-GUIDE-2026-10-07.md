# P12 DRA 10,242-HRU diagnostic execution guide — 2026-10-07

## Purpose

This guide executes the first complete population diagnostic for the modern
seven-physical-system drainage model.

It does **not** create production DRA files and it does **not** grant
`DIRECT_DRA_PRODUCER_ADMITTED`.

The diagnostic answers:

- how many of the 10,242 HRUs have 0..7 active physical systems;
- how many HRUs actually need seven-to-five compression;
- which physical systems merge in each HRU;
- the hydraulic merge-cost distribution;
- whether drainage and infiltration conductance are conserved exactly;
- whether H1 monthly levels remain complete for every active H1 HRU;
- how the current HRU P/S/T bottom authority differs from the actual LHM
  package bottom definitions.

Authority:
- `config/p12/dra-physical-systems-v2.yml`;
- `config/p12/dra-10242-diagnostic-inputs-v1.yml`;
- `docs/lhm-hru-swap/P12-DRA-SEVEN-TO-FIVE-LEVEL-DESIGN-2026-10-06.md`.

## Phase A — collect the remaining five physical source families

H1 and MVG have already passed Q4.

Run the remaining-source collector on the NHI/LHM server.

Script:

`tools/server/lwkm_collect_dra_remaining.ps1`

Model authority root:

`E:\LHM_4.3.3`

Recommended output root:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\W01_DRA_REMAINING`

Command from CMD:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\lwkm_collect_dra_remaining.ps1" ^
  -ModelRoot "E:\LHM_4.3.3" ^
  -OutputDir "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\W01_DRA_REMAINING"
```

Expected success status:

`DRA_REMAINING_Q4_IMMUTABLE_SNAPSHOT`.

Expected products include:

- `LHM433_DRA_REMAINING_Q4.zip`;
- `LHM433_DRA_REMAINING_Q4.zip.sha256`;
- `LHM433_DRA_REMAINING_Q4.zip.q4-verification.json`;
- Q2 manifest `00_manifest/files.csv`.

### Source families collected

Primary / secondary / tertiary required NHI/LHM source:
- conductance;
- infiltration factor;
- summer level;
- winter level;
- actual LHM-package bottom candidates.

Historical HRU-DRA steady-state `BODH_*1J` bottoms are probed separately and
are optional in this NHI/LHM Q4 bundle. Their absence must not make source Q4
fail.

Pipe drainage:
- conductance;
- bottom/stage.

OLF:
- conductance;
- bottom/stage.

Ground level:
- authoritative LHM MetaSWAP `ahn_f250_cm.asc`, converted explicitly to metres
  by the diagnostic.

Comparison-only inputs:
- LHM package P/S seasonal river-bottom grids.
- T package bottom needs no extra file because the supplied LHM INI binds its
  rbot to `PEIL_T1Z_250.IDF` / `PEIL_T1W_250.IDF`; the diagnostic compares
  those directly with the current HRU `BODH_T1J_250.IDF`.

No source file under `E:\LHM_4.3.3` is modified.

## Phase B — bind the population inputs

### Operational route

Use the already qualified/recovered inputs in
`config/p12/dra-10242-diagnostic-inputs-v1.yml`:

- authoritative 427,656-row `export_svat_HRU_NRU_10242.csv`;
- qualified persisted `static04_dqsat_full_10242.csv`.

The relation supplies:
- exact HRU membership;
- SVAT identity;
- x/y coordinates.

Therefore a separate SVAT-coordinate table is not required.

The persisted STATIC04 snapshot supplies the modern representative-SVAT dqsat
for every HRU.

### Audit route

Independently reproducible alternative:

- authoritative relation;
- `export_HRUschema_10242.csv` or a schema whose `svat_repr` identity is
  proven equivalent;
- qualified `grensvlak_NHIWQ_v2_fill.asc`.

The runner then calls `tools/compare_dqsat_authority.py` internally.

Expected source-side discriminator:
- 2,771 HRUs differ between legacy majority-BFE dqsat and representative-SVAT
  dqsat.

Exactly one dqsat route is allowed per diagnostic run.

## Phase C — run the population diagnostic

Tool:

`tools/diagnose_dra_10242.py`

### Operational command

```bash
python tools/diagnose_dra_10242.py \
  --relation export_svat_HRU_NRU_10242.csv \
  --dqsat-snapshot static04_dqsat_full_10242.csv \
  --h1-mvg-zip LHM433_H1_MVG_Q4.zip \
  --remaining-zip LHM433_DRA_REMAINING_Q4.zip \
  --stage-start 1971-01-01 \
  --stage-end 2022-01-01 \
  --output-dir dra_10242_diagnostic
```

### Source-reconstruction audit command

```bash
python tools/diagnose_dra_10242.py \
  --relation export_svat_HRU_NRU_10242.csv \
  --schema export_HRUschema_10242.csv \
  --dqsat-grid grensvlak_NHIWQ_v2_fill.asc \
  --h1-mvg-zip LHM433_H1_MVG_Q4.zip \
  --remaining-zip LHM433_DRA_REMAINING_Q4.zip \
  --stage-start 1971-01-01 \
  --stage-end 2022-01-01 \
  --output-dir dra_10242_diagnostic_source_rebuild
```

## Hard gates

The diagnostic fails closed unless:

- membership rows = 427,656;
- distinct HRUs = 10,242;
- representative dqsat contains exactly the same 10,242-HRU domain;
- every member coordinate resolves to drainage-grid geometry;
- every active physical system has the required hydraulic attributes;
- every active H1 member has every requested monthly stage;
- no forbidden hydraulic-class merge is needed;
- all compression lineage is conserved;
- drainage conductance is conserved within numerical tolerance;
- infiltration conductance is conserved within numerical tolerance.

No H1 source fallback is introduced. Known H1 source exceptions currently have
zero coordinate matches in both recovered SVAT populations, but the runner
still fails if one occurs in the admitted relation.

## Outputs

`summary.json`
- overall pass/fail;
- exact SHA-256 of every run-bound population/source artifact;
- population-input mode / dqsat authority;
- HRU counts;
- active-system count distribution;
- HRUs requiring compression;
- merge count and maximum merge cost;
- maximum conductance-conservation error;
- P/S/T bottom-authority comparison when historical J-bottom evidence is available;
- drainage-versus-infiltration equivalent-level tension for every compressed
  infiltration-capable merge.

`hru_summary.csv`
- one row per successfully diagnosed HRU;
- member count;
- number of active physical systems;
- number of SWAP levels;
- compression required yes/no;
- merge count;
- merge cost;
- conductance errors;
- final physical-source grouping.

`merge_events.csv`
- every physical merge;
- left/right lineage;
- hydraulic cost;
- final group;
- dynamic-level record count.

`failures.csv`
- every HRU that fails closed and the exact reason.

## Interpretation gate

A technically successful diagnostic is not sufficient for production admission.

After the run, review at least:

1. fraction of HRUs requiring compression;
2. dominant merge pairs;
3. high-cost/outlier merges;
4. every merge involving H1;
5. every HRU with seven active systems;
6. P/S/T bottom-authority differences;
7. conservation residuals;
8. drainage-versus-infiltration equivalent-level gap p50/p90/p95/p99/max,
   especially H1 merges;
9. failed HRUs, if any.

Only after that review can the compression policy be admitted or revised.

## Current state before execution

- seven-system physical model: implemented;
- H1/MVG Q4: passed;
- H1 monthly sequence: exact/gap-free in recovered bundle;
- known H1 source exceptions: zero matches in recovered SVAT populations;
- remaining P/S/T/PIPE/OLF source Q4: pending server execution;
- 10,242 diagnostic code: implemented;
- production DRA admission: **not granted**.


## Terminal H1 level guard

The production simulation ends on 2021-12-31.

The recovered H1 source has a qualified 2022-01-01 monthly stage. The
diagnostic therefore includes that source record as the terminal H1
`DATOWL/LEVEL` point.

This avoids depending on any SWAP `afgen` extrapolation beyond the last
level-table date. Every simulated instant lies within the explicit H1 level
table support.


## Conductance-only preflight

If the remaining Q4 bundle does not contain the optional historical
`BODH_P1J_250.IDF`, `BODH_S1J_250.IDF` or `BODH_T1J_250.IDF`, first run:

`tools/diagnose_dra_activity_10242.py`.

This preflight requires only:
- the 427,656-row authoritative relation;
- H1/MVG Q4;
- remaining-source Q4 conductance files.

It still produces the decisive population facts:
- active-system count distribution 0..7;
- active HRUs per physical system;
- HRUs requiring more than five SWAP levels;
- dominant active-system combinations.

It does not invent a replacement P/S/T static bottom and therefore does not
claim full DRA hydraulic admission.

The full `diagnose_dra_10242.py` run remains the next gate once a qualified
static P/S/T bottom authority is available.
