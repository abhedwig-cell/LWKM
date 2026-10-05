# W01 server topology discovery — 2026-10-05

## Observed server evidence

Observed server tree:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM`

A recursive filename search for `svat.asc` exposed the following LWKM-period candidates:

- `run_1970_1979\metaswap\svat.asc`
- `run_1980_1989\metaswap\svat.asc`
- `run_1990_1999\metaswap\svat.asc`
- `run_2000_2009\metaswap\svat.asc`
- `run_2010_2019\metaswap\svat.asc`
- `run_2020_2022\metaswap\svat.asc`
- `run_2023_2024\metaswap\svat.asc`
- `run_2025_2025\metaswap\svat.asc`

The same tree also contains overlapping/alternative candidates:

- `run_2010_2021_MS_daily\metaswap\svat.asc`
- `run_2020_2024_MS_daily\metaswap\svat.asc`

Other non-LWKM run families also exist under the wider
`G:\Projecten\2025\Release_LHM433\modelruns\runs` tree.

## Qualification consequence

Do **not** declare the whole `runs_LWKM` directory as one authoritative RUN root yet.

The directory contains mutually overlapping run candidates. A recursive source inventory over the entire parent tree could silently mix source files from different scientific runs.

W01 therefore receives a preliminary gate:

`Q0A_RUN_CHAIN_DISCOVERY`.

Q0A must identify:

1. the ordered period-run chain that actually produced the target LWKM source state;
2. any restart/continuation relationship between periods;
3. whether the `MS_daily` alternatives supersede, complement or are unrelated to the decadal runs;
4. whether static MetaSWAP inputs such as `svat.asc` are byte-identical across selected periods;
5. the control/config file associated with every selected period.

Only then may Q0 bind the authoritative run chain.

## Immediate diagnostics

The next server diagnostics are metadata-only and do not modify source data.

### A. Hash every LWKM svat.asc

Compare SHA-256 of all `runs_LWKM\run_*\metaswap\svat.asc` files.

If all selected production periods share one hash, that is evidence for one stable SVAT schematisation across the chain. If hashes differ, period-specific static state must be represented explicitly.

### B. Find run controls/configuration

For every `run_*` directory, inventory likely run-defining files in the run root and first-level control/config directories.

The purpose is not to guess authority by filename. It is to bind each candidate period to the files that launched/configured it.

### C. Do not yet use LWKM_run_resultaten_totaal as raw RUN authority

The current command prompt directory:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`

looks like an aggregated results directory by name. It may be an important downstream output source, but it is not admitted as the raw authoritative LHM run root without additional evidence.

## Status

`W01 = Q0A_RUN_CHAIN_DISCOVERY_IN_PROGRESS`

No Q0 run identity has been admitted yet.


## Q0A result — stable SVAT schematisation across all candidate LWKM runs

Server-side SHA-256 inventory on 2026-10-05 found the same byte identity for every exposed LWKM `metaswap\svat.asc`:

`BFB8A580C9DE2B3D3C7966A29B4B9FDD3491F6CA52D0D3494F0400CD1A8A812A`

File size for every copy:
`12,482,732 bytes`.

Confirmed candidates:
- run_1970_1979
- run_1980_1989
- run_1990_1999
- run_2000_2009
- run_2010_2019
- run_2010_2021_MS_daily
- run_2020_2022
- run_2020_2024_MS_daily
- run_2023_2024
- run_2025_2025

Qualification consequence:

`SVAT_ASC_MULTI_RUN_BYTE_IDENTITY_CONFIRMED`.

This is evidence for one stable SVAT schematisation across both the standard period runs and the overlapping MS_daily alternatives. It does not select the authoritative dynamic run chain.

Filesystem timestamps differ and are not treated as content authority.

## NHI-server scope correction

Project owner confirmed that HRU/SWAP producer material is not located on the NHI server.

Therefore W01 NHI-server provenance must not require:
- HRU2SWAP executable/log;
- HRU/SWAP launch batch;
- HRU/SWAP control file;
- SWP template;
- downstream HRU/SWAP-specific lookups merely because they exist in reconstructed LWKM evidence.

Those belong to a separate downstream provenance route.

W01 is restricted to:
1. authoritative LHM/MODFLOW/MetaSWAP run output;
2. run-bound/static NHI model inputs actually present and consumed from the NHI server;
3. run control/restart evidence needed to bind the selected LHM run chain.

## Next Q0A question

Identify the actual period-run chain used to construct `LWKM_run_resultaten_totaal`.

Do not infer this from directory names alone. Prefer:
- batch/PowerShell/control scripts;
- explicit references in aggregation commands;
- run-specific control files;
- restart/continuation metadata.

Status remains:
`Q0A_RUN_CHAIN_DISCOVERY_IN_PROGRESS`.


## Q0A finding — LWKM_run_resultaten_totaal/modflow/copy.bat does not establish source assembly

Search in `LWKM_run_resultaten_totaal` found references to `run_2010_2019` only in:

`LWKM_run_resultaten_totaal\modflow\copy.bat`.

Observed semantics:

- lines 1-6 and 9-11 are commented-out copy commands;
- active lines 7-8 copy `bdgriv_sys5_201*_l2.IDF` and `bdgriv_sys6_201*_l2.IDF`;
- the copy direction is from the current aggregated-results-side `bdgriv` directory to
  `run_2010_2019\modflow\results\bdgriv\`.

Therefore this batch file is **not** evidence that `LWKM_run_resultaten_totaal` was assembled from `run_2010_2019`.

Qualification:

`COPY_BAT_RUN_CHAIN_AUTHORITY_FALSIFIED_FOR_SOURCE_ASSEMBLY`.

It may document a maintenance/back-copy operation and remains provenance evidence, but it must not be used to select the authoritative run chain.

Next evidence required:
1. full per-run control/config inventory;
2. product/year coverage inside `LWKM_run_resultaten_totaal`;
3. scripts outside the total-results tree that explicitly construct or update that tree;
4. restart/continuation metadata per period run.
