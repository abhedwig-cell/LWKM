# Datamodel to SWP field contract

Status levels:
- DIRECT: explicit datamodel value maps directly.
- DOMAIN_JOIN: value comes from a referenced domain table.
- PROFILE_DEFAULT: application profile supplies an explicit value.
- DERIVED: deterministic rule over datamodel values.
- UNRESOLVED: legacy output observed but datamodel rule not yet bound.

## Current contract

| SWP field/block | authority | status |
|---|---|---|
| soil profile rows | Runs.bodem_id + Runs.dikte_id -> discretisatie | DOMAIN_JOIN |
| hydraulic rows | Runs.bodem_id -> eigenschappen | DOMAIN_JOIN |
| texture rows | Runs.bodem_id -> eigenschappen | DOMAIN_JOIN |
| SWBOTB | Runs.SWBOTB | DIRECT |
| bottom series | run/boundary tables when SWBOTB=2 | DOMAIN_JOIN, exact join pending |
| crop/rotation identity | Runs.crop_id / rotation_id | DIRECT |
| RDS | Runs/Wortelzone relationship | UNRESOLVED |
| ELAS | not present in inspected eigenschappen schema; LWKM legacy output 1e-6 | PROFILE_DEFAULT pending explicit datamodel field |
| TSTART/TEND | legacy output 1971-01-01 / 2021-12-31 | PROFILE_DEFAULT pending datamodel binding |
| METFIL | meteo identity/reference | DOMAIN_JOIN, filename policy must be separate from data |
| SWDRA/DRFIL | run/scenario drainage settings | partially bound; no implicit empty file |
| SWBBCFILE/BBCFIL | boundary-file settings | partially bound; no implicit empty file |
| crop rotation rows | crop/rotation tables | DOMAIN_JOIN |
| CO2 file | shared scenario/crop asset | DOMAIN_JOIN/reference, never implicit copy |

## Rule

Filename construction is serialization policy, not physical/model data. Do not store run-specific filenames as scientific authority when a stable asset/reference key can be used instead.

The generic context should expose semantic objects (meteo series id, drainage definition id, crop rotation id, boundary definition id). The template/export layer resolves paths.
