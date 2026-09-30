# Server logistics status

Status:
**QUALIFIED IMPLEMENTATION CANDIDATE, REAL-SERVER ADMISSION PENDING**

READY:
- LHM control files are primary configured-source provenance;
- recursive control discovery for `control_run_YYYY_YYYY.ini`;
- strict period ordering with gap/overlap rejection;
- alias/path resolution;
- wildcard expansion for configured annual source families;
- cross-control stable/varying comparison;
- meteo-year dependency detection;
- explicit static/period/run-output/restart classes;
- exact downstream run-output allowlist in the LHM 4.3.3 transfer profile;
- direct `controls + profile -> resolved plan -> verified bundle` CLI path;
- portable v2 ZIP manifest with SHA-256;
- content-addressed payload deduplication;
- bundle integrity verification;
- verify-before-unpack;
- immutable snapshot policy;
- restart payload excluded while original controls retain restart lineage.

Current server command:

```text
python -m tools.lwkm_source_cli collect \
  --controls <authoritative-LHM-run-tree> \
  --profile config/server/lhm433-lwkm-transfer-profile.yml \
  --output <bundle.zip>
```

Optional dry/inspection step:

```text
python -m tools.lwkm_source_cli plan \
  --controls <authoritative-LHM-run-tree> \
  --profile config/server/lhm433-lwkm-transfer-profile.yml \
  --output <resolved-plan.json>
```

The collector fails before bundling when:
- control periods overlap or have gaps;
- a required configured key is absent/unresolved;
- a configured wildcard matches no source file;
- the original run root cannot be identified;
- a required run-output family matches no file.

## Exact raw run-output boundary

The transfer profile now admits raw producer inputs only:

MODFLOW:
- head layer 1;
- head layer 2;
- river budgets systems 1-6, layers 1 and 2;
- drainage budgets systems 1-3, layer 1;
- vertical face-flow layer 1 for audited diagnostic/water-balance derivations.

MetaSWAP:
- bdgPm;
- bdgPssw;
- bdgPsgw;
- bdgETact;
- bdgqrun;
- bdgqmodf;
- bdgdecStot;
- msw_Ebs;
- msw_Esp;
- msw_Epd;
- msw_Eic;
- msw_Tact.

Derived period products such as `bdgqmsw`, `bdgqlat`, climate summaries, fuzzy classes and archive RAR files are not source authority and are not part of the raw transfer boundary.

## Historical orchestration audit

Recovered and inspected:
- `exe.zip`;
- historical loose batch scripts;
- Fortran source archive.

Established:
- `modflowidf2asc.exe` aggregates MODFLOW daily IDFs;
- `gridcalc.exe` performs grid algebra/period aggregation;
- `grid_adjust.exe` is used in GVG processing;
- RAR scripts are archival cleanup only.

Two historical batch defects are explicitly preserved as defects rather than silently repaired:
- GVG script uses an unbound `%mm%` in its visible active path;
- `do_modflow_sumrivdrndec.bat` consumes `outf1` while its visible producer expression is commented out.

## Pending real-server evidence

Still required before Q4 / `LWKM_SOURCE_QUALIFIED`:
1. raw access to the complete actual control chain on the authoritative NHI/LHM run tree;
2. one real run of `plan` confirming the exact periods and all configured annual sources;
3. one real `collect` producing a verified bundle;
4. upstream run-completeness evidence sufficient for Q1-Q3;
5. consumer smoke test from the unpacked immutable snapshot.

The Project copy `control_runs.zip` remains located but its raw backing bytes are not currently authorized for materialization. This does not block the implementation candidate, but it prevents claiming the exact six-period chain as verified repository authority from this environment.

DO NOT BLOCK ON:
- rewriting existing Fortran executables;
- reproducing the entire LHM server directory;
- taking ownership of MODFLOW restart mechanics;
- copying restart payload that downstream LWKM does not consume.

TARGET:
one server-side collect command produces one verified portable bundle; downstream LWKM work starts only from a verified immutable snapshot.
