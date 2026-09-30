# Datamodel to SWP field contract

Status levels:
- DIRECT: explicit datamodel value maps directly.
- DOMAIN_JOIN: value comes from a referenced datamodel table.
- CONFIG: explicit application/run configuration value.
- SERIALIZATION: filename/formatting policy over already resolved semantics.
- QA_ONLY: useful historical cross-check, not production authority.
- UNRESOLVED: legacy output observed but the production rule is not yet bound.

## Current production contract

This contract is based on the recovered `Datamodel_10242.sqlite` from the historical `Datamodel_9830.zip` archive plus the already-established P12 authority contracts.

Recovered SQLite SHA-256:
`4b697e7f806d0e6f0c345b92bb78c456238c3af5634559a7e2f7edd4171183bb`

The raw archive is historical evidence. The current Project `Datamodel_10242.xlsx` has the same size and matching indexed content, but its Project backing bytes cannot currently be materialized, so byte identity has not been asserted.

| SWP field/block | authority | status |
|---|---|---|
| TSTART / TEND | Runs.TSTART / Runs.TEND | DIRECT, numeric day offset serialized to ISO date |
| INLIST_CSV | Output selected by Runs.crop_id | DOMAIN_JOIN |
| NUMNODNEW | Runs.NUMNODNEW | DIRECT |
| DZNEW | DZNEW selected by Runs.dikte_id | DOMAIN_JOIN |
| METFIL | Runs.METFIL | DIRECT file reference |
| SWETR | Runs.SWETR; modern upstream producer derives it from authoritative representative land use | DIRECT at renderer boundary |
| crop rotation rows | Gewasrotatie selected by Runs.climate_id + crop_id + rotation_id | DOMAIN_JOIN |
| SWINCO / GWLI | Runs.SWINCO / Runs.GWLI | DIRECT |
| PONDMX / RSRO | Runs.PONDMX / Runs.RSRO | DIRECT |
| RSOIL | Gewasweerstand selected by Runs.crop_id | DOMAIN_JOIN |
| soil profile rows | discretisatie selected by Runs.bodem_id + dikte_id | DOMAIN_JOIN |
| hydraulic rows | eigenschappen selected by Runs.bodem_id | DOMAIN_JOIN |
| ELAS | eigenschappen.ELAS | DOMAIN_JOIN, explicit datamodel value |
| texture rows | eigenschappen selected by Runs.bodem_id | DOMAIN_JOIN |
| RDS | Runs.RDS | DIRECT production authority |
| Wortelzone.RDS | Wortelzone selected by soil_id + croporg_id | QA_ONLY |
| SWDRA | Scenario selected by Runs.scenario_id | DOMAIN_JOIN |
| DRFIL | Runs.DRFIL | DIRECT file reference |
| SWBBCFILE / BBCFIL / SWBOTB | Runs fields | DIRECT |
| BBC time series | separate BBC producer/file | outside main-SWP renderer |
| DRA content | separate DRA producer/file | outside main-SWP renderer |
| MET content | separate MET producer/file | outside main-SWP renderer |

## 10,242-run completeness audit

The recovered SQLite contains 10,242 Runs rows. The renderer-domain audit gives zero missing cases for:
- discretisatie;
- eigenschappen;
- Gewasrotatie;
- Output;
- Gewasweerstand;
- Scenario;
- DZNEW count versus NUMNODNEW;
- ELAS null values.

Observed run distributions:
- scenario_id: `direct` for 10,242;
- SWINCO: 2 for 10,242;
- SWBBCFILE: 0 for 2,067 and 1 for 8,175;
- SWBOTB: 7 for 2,067 and 2 for 8,175;
- SWETR: 0 for 7,162 and 1 for 3,080;
- irrigation_id: 0 for 9,321, 1 for 637 and 2 for 284;
- TSTART: day offset 365 for all 10,242;
- TEND: day offset 18,992 for all 10,242.

The historical Wortelzone join is complete but disagrees with Runs.RDS for 4,350 of 10,242 runs. This is not a renderer ambiguity. P12 authority is the representative HRU schema, propagated into Runs.RDS. Wortelzone is therefore diagnostic only and must not silently override Runs.RDS.

## Important historical-template finding

The recovered older `swap_wwl.swp` is useful as a mapping oracle but is not production template authority. It hard-codes active `SWETR = 0`, while the current 10,242 datamodel contains 3,080 runs with SWETR = 1. Using that old template unchanged would therefore erase real run variability.

The current direct renderer must expose SWETR as a resolved context value. Actual current `Template.zip` remains a regression/provenance source once its raw backing bytes are accessible.

## Serialization rule

A run-specific filename such as `2000.met`, `2000` for DRA, or `2000` for BBC is a reference to separately produced content. The renderer may serialize the reference, but it must not regenerate the MET/DRA/BBC scientific content.

Unknown template symbols remain fatal. The template layer is not allowed to recompute HRU majorities, soil classes, land-use flags, rooting depth or boundary science.
