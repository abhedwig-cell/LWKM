# W07 remaining drainage-source Q4 execution guide — 2026-10-07

## Purpose

Close source-byte provenance for the five drainage families that complement the
already Q4-qualified H1/MVG bundle:

- primary;
- secondary;
- tertiary;
- pipe drainage;
- OLF/overland flow;
- plus the LHM ground-level grid used by the HRU aggregation.

Tool:

`tools/server/lwkm_collect_dra_remaining.ps1`.

## Authority split

Required source files come from the real LHM433 input authority under:

`E:\LHM_4.3.3\Data\2_Model_Input`.

The collector also probes for:

- `BODH_P1J_250.IDF`;
- `BODH_S1J_250.IDF`;
- `BODH_T1J_250.IDF`.

These three are **not required NHI/LHM inputs**. They originate from the
historical HRU-DRA control and are only optional W07 comparison evidence.

If they happen to be present under the LHM model root, the collector includes
them and records that fact. If they are absent, Q4 must still succeed.

## Fetch the current collector directly

From CMD on the NHI server, this downloads the exact current branch version
into `LWKM_tools` using Windows PowerShell 5.1:

```bat
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/abhedwig-cell/LWKM/work/lhm-hru-swap-workflow-v1/tools/server/lwkm_collect_dra_remaining.ps1' -OutFile 'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\lwkm_collect_dra_remaining.ps1'"
```

Then verify that the file exists:

```bat
dir "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\lwkm_collect_dra_remaining.ps1"
```

If outbound GitHub access is blocked on that server, use the repository file
`tools/server/lwkm_collect_dra_remaining.ps1` through the normal browser/file
transfer route instead. Do not substitute an older local copy without checking
its content identity.

## Server command

Place the current repository version of:

`tools/server/lwkm_collect_dra_remaining.ps1`

in:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools`.

Run from CMD:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\lwkm_collect_dra_remaining.ps1" ^
  -ModelRoot "E:\LHM_4.3.3" ^
  -OutputDir "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\W07_DRA_REMAINING"
```

Expected success status:

`DRA_REMAINING_Q4_IMMUTABLE_SNAPSHOT`.

Expected output:

```text
W07_DRA_REMAINING\
  LHM433_DRA_REMAINING_Q2\
  LHM433_DRA_REMAINING_Q4.zip
  LHM433_DRA_REMAINING_Q4.zip.sha256
  LHM433_DRA_REMAINING_Q4.zip.q4-verification.json
```

The collection JSON also reports whether each optional historical J-bottom was:

- `RECOVERED_AT_LHM_MODELROOT`; or
- `NOT_PRESENT_AT_LHM_MODELROOT`.

Q4 success is deliberately independent of those optional files because they are
not LHM-package source authority.

The 10,242 full diagnostic no longer requires these historical J-bottoms.

Modern P/S/T static-bottom diagnostic authority is derived from the actual LHM
package summer/winter bottoms:

- baseline candidate: equal-season arithmetic mean;
- sensitivity bound 1: deepest seasonal bottom;
- sensitivity bound 2: shallowest seasonal bottom.

This is appropriate for diagnosis because the LHM package uses equal half-year
summer/winter periods, while SWAP method 3 exposes one static ZBOTDR per level.
The mean is therefore the least-squares equal-season static candidate. It is
**not yet production-admitted**.

If all three historical `BODH_*1J` files are recovered, the diagnostic adds a
fourth historical comparison automatically. If they are absent, the modern
diagnostic still runs and Q4 remains valid.

Never substitute an LHM seasonal package bottom and label it as the historical
J-bottom.

## Required upload after success

Preferred:

`LHM433_DRA_REMAINING_Q4.zip`.

Also useful but normally embedded in the ZIP:

- `00_manifest/files.csv`;
- `00_manifest/collection.json`;
- the Q4 verification JSON.

## What happens next

Once the ZIP is available, the W07 population diagnostic is ready in:

`tools/diagnose_dra_10242.py`.

Already bound population inputs:

- `/LWKM/export_svat_HRU_NRU_10242.csv` — 427,656 membership rows;
- `/LWKM/static04_dqsat_full_10242.csv` — qualified representative-dqsat replay for 10,242 HRUs;
- Q4 H1/MVG bundle.

The diagnostic computes:

- active physical-system count per HRU;
- HRUs requiring 7→5 or 6→5 compression;
- all merge pairs and lineage;
- merge-cost quantiles;
- H1 merge frequency;
- exact drainage/infiltration-conductance conservation;
- deterministic level order;
- P/S/T LHM seasonal-bottom spread;
- sensitivity of 7→5 grouping to mean/deepest/shallowest package-bottom
  reduction;
- historical J-bottom comparison when those optional bytes are available;
- counts of levels that legacy v0.38 would deactivate at DRARES > 20000 d;
- fail-closed SWAP DRARES > 1e5 interface overflow.

No production DRA admission follows automatically from this diagnostic.
