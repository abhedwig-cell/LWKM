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
