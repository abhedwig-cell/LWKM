# W01-O Deltares output authority inventory result — 2026-10-05

## Result

`OUTPUT_AUTHORITY_INVENTORIED_NOT_FILE_QUALIFIED`

Authoritative root:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`

Project-owner authority states that this tree is the Deltares-collected LHM output source for LWKM.

The uploaded inventory bundle has SHA-256:

`161bf03b4a0fc7dda1a9335978b8a0da210d3297420b18da90ac458148215c7d`.

It contains metadata only, not the model output payload.

Persisted machine-readable evidence:

`docs/evidence/2026-10-05/w01-output-inventory-summary.json`.

## Scale

The authority tree contains:

- 399,184 files;
- 2,874,213,809,597 bytes, approximately 2.87 TB;
- 329,250 IDF files;
- 49,781 ASC files;
- 19,140 LOG files;
- 568 CSV files.

Top-level split:

| Top folder | Files | Bytes | Role |
| --- | ---: | ---: | --- |
| `modflow` | 287,403 | 1,555,035,862,322 | primary LHM/MODFLOW output candidate |
| `metaswap` | 42,206 | 224,591,756,994 | primary LHM/MetaSWAP output candidate |
| `postprocessing` | 69,575 | 1,094,586,190,281 | derived/historical postprocessing evidence |

The full tree must **not** be treated as one flat set of equivalent basis files.

## Primary source versus derived oracle

### MODFLOW and MetaSWAP

For the modern reconstructed chain, raw `modflow` and `metaswap` products are the primary W01-O candidate source layer.

Every file actually consumed by W02 or later still requires:
- SHA-256;
- semantic role;
- temporal support;
- units/support contract;
- downstream consumer;
- qualification evidence.

Discovery in the authority tree is not production admission.

### postprocessing

The `postprocessing` tree contains historical derived products, logs, tools and diagnostics.

It is valuable as:
- historical execution evidence;
- golden regression oracle;
- compatibility reference.

It must not silently become primary source authority when the same product is reproducibly derived from qualified MODFLOW/MetaSWAP outputs.

This is especially important for `postprocessing\wb`, which contains many derived annual, seasonal, quarter and decade water-balance products.

## MODFLOW findings

### head

Inventory:
- 47,419 files;
- approximately 277.1 GB;
- observed 1970 through 2024.

Layer 1 has daily coverage across the observed 1970-2024 period.

For 1970-2022 the historical naming uses timestamps such as:

`head_19700101000000_l1.IDF`.

For 2023-2024 layer-1 files use names such as:

`head_20230101_l1.idf`.

Deeper layers have a lower output cadence and must be qualified only if a downstream consumer needs them.

### bdgflf

Inventory:
- 44,929 files;
- approximately 229.9 GB;
- observed 1970 through 2024.

The tree contains two materially different routes:

1. uncorrected/root `bdgflf`;
2. `bdgflf\diepe_slootkwel_gecorrigeerd`.

For 1970-2022 both uncorrected and corrected layer-1 daily series are exposed.

The 2023-2024 root output changes representation to partitioned members such as:

`bdgflf_20230101_l1_p000.idf` through `p007`.

Do not treat the 2023-2024 partitioned representation as silently identical to the historical merged IDF format.

Ownership of corrected versus uncorrected FLF remains an explicit downstream qualification decision.

### bdgriv

Inventory:
- 116,148 IDFs;
- approximately 678.9 GB;
- observed 1970 through 2022.

The structure is exactly consistent with six systems:
- systems 1-4 in layer 1;
- systems 5-6 in layer 2.

Project production authority now requires **all RIV interaction in layer 1**. Therefore systems 1-4 are mandatory members of the W02 layer-1 surface-water interaction source set. Systems 5-6 remain separate layer-2 provenance and are not part of that layer-1 net term.

Each system has 19,358 observed daily dates over 1970-2022.

No 2023-2024 `bdgriv` continuation was identified by this inventory.

### bdgdrn

Historical `bdgdrn`:
- 58,074 IDFs;
- approximately 339.4 GB;
- observed 1970 through 2022;
- systems 1-3 in layer 1.

Project production authority requires all three layer-1 DRN systems to be included:
1. pipe drainage;
2. MVG/simplified surface ditches;
3. OLF/overland flow.

A separate `bdgdrn_org` tree exists for 2023-2024:
- 17,544 IDFs;
- approximately 10.5 GB;
- partitioned representation.

This later representation is not qualified as a drop-in continuation of historical `bdgdrn`.

## MetaSWAP findings

The core decade-style output is well represented over 1970-2024.

For the standard core series, 36 dates per year are observed.

Available raw series include:

- `msw_Ebs`;
- `msw_Esp`;
- `msw_Epd`;
- `msw_Eic`;
- `msw_Tact`;
- `bdgPm`;
- `bdgPssw`;
- `bdgPsgw`;
- `bdgETact`;
- `bdgQrun`;
- `bdgQmodf`;
- `bdgdecStot`;
- `msw_Qinf`;
- `msw_Tpot`.

There are also additional/specialized series such as:
- `bdgQrunm3_daily` for 2010-2021;
- WOFOST output series for later periods.

Those are not yet classified as production inputs for the current LWKM hydrology chain.

## Important qmsw/qlat correction

No raw MetaSWAP subfolders named `bdgqmsw` or `bdgqlat` were found.

Both names occur extensively under:

`postprocessing\wb`.

Existing source documentation for the reconstructed postprocessing chain treats:
- `bdgqmsw` as a derived exchange term;
- `bdgqlat` as a derived lateral term.

Therefore the W01-O inventory supports:

`BDGQMSW_BDGQLAT_DERIVED_NOT_RAW_METASWAP_SOURCE`.

This corrects any earlier source specification that implicitly treated those products as raw MetaSWAP output.

## Period boundary that must remain explicit

The authority tree is not temporally homogeneous:

- core MetaSWAP series: observed through 2024;
- MODFLOW head layer 1: observed through 2024;
- root bdgflf: observed through 2024, with a format change in 2023;
- historical bdgriv/bdgdrn: observed only through 2022;
- historical `postprocessing\wb`: predominantly 1970-2022.

Therefore no single `1970-2024` production period may be assumed for all water-balance products.

The production period must be defined per consumer and source family.

## What is now closed

Closed at discovery level:

- authoritative Deltares output root bound;
- full output tree metadata inventory obtained;
- top-level raw/derived separation established;
- major MODFLOW and MetaSWAP families identified;
- qmsw/qlat classified as derived rather than raw MetaSWAP subfolders;
- 2023-2024 representation changes exposed rather than hidden.

## What is not yet closed

Still required before W01-O file admission:

1. bind the exact files consumed by each downstream step;
2. decide the admitted production period for each consumer;
3. decide corrected versus uncorrected FLF ownership;
4. qualify later partitioned formats if 2023-2024 is needed;
5. hash every consumed file;
6. validate format/geometry/units for every consumed file family;
7. persist a file-level qualification registry.

## Next step

Do not hash all 2.87 TB blindly.

First construct the **consumer-bound source set** from the actual admitted/reconstructed postprocessing and HRU workflow.

Then hash and qualify only:
- files required to reproduce the production chain;
- plus separately selected historical oracle outputs needed for regression.

This preserves the project rule:

`100% OF CONSUMED FILE IDENTITIES QUALIFIED`

without turning every diagnostic/log/duplicate file in the authority tree into production authority.


## Layer-1 RIV/DRN production correction — 2026-10-05

Project authority requires complete MODFLOW layer-1 RIV/DRN interaction.

Authority:
`docs/server/W02_LAYER1_SURFACE_WATER_INTERACTION_CONTRACT_2026-10-05.md`.

For the 1970-2022 source tranche:
- RIV layer 1: systems 1-4 = 77,432 files;
- DRN layer 1: systems 1-3 = 58,074 files;
- RIV systems 5-6 = layer 2 and are excluded from the layer-1 net contract.

This revises the earlier provisional source-tranche estimate from 235,834 files / 1.368 TB to:

- 197,118 files;
- 1,142,039,024,280 bytes;
- approximately 1.142 TB;

assuming one selected FLF route and the current 12 MetaSWAP core families.

The historical/reconstructed all-RIV-system sum is not production-authoritative for a layer-1 balance.
