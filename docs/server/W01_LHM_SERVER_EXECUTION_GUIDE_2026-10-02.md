# W01 execution guide — LHM provenance

Updated: 2026-10-05

## Authority

Current authority:
- `docs/server/W01_LHM_AUTHORITY_SPLIT_2026-10-05.md`
- `config/source/w01-lhm-authority-v1.yml`
- `docs/governance/LWKM_FILE_QUALIFICATION_POLICY_2026-10-02.md`

## W01 is split in two

### W01-O — authoritative LHM output

Project-owner authority identifies the Deltares-collected output tree as:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`

This tree is the output provenance boundary for the reconstructed LWKM chain.

Do not reconstruct the underlying `run_*` assembly as a prerequisite.

Tool:
`tools/server/lwkm_output_inventory.ps1`.

### W01-I — authoritative LHM input configuration

The project-owner supplied LHM control `.ini` files are the input-configuration authority.

Tool:
`tools/server/lwkm_ini_provenance.ps1`.

The INI route extracts:
- all configuration assignments;
- ConfigObj-style interpolated paths;
- path-like input/resource candidates;
- restart declarations;
- executable bindings;
- INI SHA-256 when raw bytes are available.

A declared path is not automatically a qualified historical file. Referenced files are qualified separately.

## First server action: inventory the authoritative output tree

No Python is required.

From Command Prompt, with the PowerShell script available in the LWKM tools directory:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\lwkm_output_inventory.ps1" ^
  -Root "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal" ^
  -OutputDir "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\W01_output_inventory"
```

This is read-only.

It produces:
- `output-inventory.csv`;
- `output-folder-summary.csv`;
- `output-summary.json`.

Return these three small metadata files for qualification review.

## What this first inventory does not do

It deliberately does not:
- hash every output file;
- copy the output tree;
- create a ZIP;
- infer which files are consumed by LWKM;
- infer the internal Deltares period-run assembly.

First we identify the exact output products and consumers. Then every consumed file receives:
- SHA-256;
- semantic role;
- temporal/unit contract;
- downstream consumer;
- qualification evidence.

## Input-config action

The currently exposed loose Project/Library file is:
`control_run_1970_1979.ini`.

Existing project/Library/archive evidence must be exhausted for additional supplied control INIs before asking for any re-upload.

When raw INI files are available in a directory, run:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "lwkm_ini_provenance.ps1" ^
  -IniPath "control_run_1970_1979.ini" ^
  -OutputDir "W01_ini_inventory"
```

For multiple files:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "lwkm_ini_provenance.ps1" ^
  -IniPath "control_run_1970_1979.ini","control_run_1980_1989.ini" ^
  -OutputDir "W01_ini_inventory"
```

Outputs:
- `ini-manifest.csv`;
- `ini-assignments.csv`;
- `ini-path-candidates.csv`;
- `ini-summary.json`.

## Admission sequence

W01 is closed only after:

1. W01-O authority root is inventoried;
2. every output file actually consumed downstream is individually qualified;
3. all supplied LHM INI authorities are catalogued;
4. required INI-referenced inputs are bound to qualified identities where relevant;
5. output and input/config evidence is frozen into immutable manifests/bundles.

Target:

`100% OF CONSUMED FILE IDENTITIES QUALIFIED`.

## Explicit separation

Do not require the NHI server to contain:
- HRU2SWAP executable/log;
- HRU/SWAP control/batch files;
- SWP template;
- downstream HRU/DRA/BBC/MET runtime assets.

Those belong to later provenance gates.
