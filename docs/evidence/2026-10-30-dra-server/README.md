# Direct-source DRA server producer, actual population evidence, 2026-10-30

The new NumPy-only server producer generated 10,242 actual DRA files using
Q4-identified source bytes, current HRU identities/membership and the identified
dqsat raster. Period 1970-01-01 to 2022-12-31, 637 actual monthly H1 points
through the interpolation endpoint 2023-01-01. No annual-cycle extrapolation.
All files passed independent scalar, horizon-count, spacing and date-coverage
checks. No new SWAP execution or hydrological admission is claimed.

Methods: 4,778 without compression; 5,435 protected; 29 AUTO_APPROXIMATED_FIVE_LEVEL.
Before compression: 1,815 owner-rule drainage omissions and 2,905 infiltration
branch disablements. Static parameters of all seven systems in every HRU were
compared against the archived C2 full records: no change above relative tolerance
1e-9*max(1,abs(reference)). Maxima are recorded without rounding in summary.json.
Existing archived C2 DRA bytes were not rewritten. These new full-period files
have a different monthly axis; byte identity with a 13-point C2 year is not claimed.

Actual first full build: 72.642890948 seconds locally. Repetition: 11.499867602
seconds, all 10,242 HRUs and 637 H1 months reused with input/output hash checks.
Serialized DRA size: 139,642,358 bytes. Timing is host-specific and not a Windows
server performance prediction. A preliminary actual-source 1971 population run
also produced 10,242 files with 29 approximations and zero errors.

122 targeted tests passed across shared aggregation, owner rules, compression,
full-axis vectorized objective, DRA serialization, server generation/restart,
source/cache corruption checks, existing DRA interfaces and SWP regression.
The packaged import closure was checked while explicitly forbidding pandas.
Local runtime: Python 3.12, NumPy 2.3.5. Actual Windows server execution on Python
3.10.8 / NumPy 1.23.5 is the next qualification step.

Source registry: config/dra/server_sources_20261030.json. Its original Windows
paths and hashes are taken from the Q4 files.csv of LHM433_H1_MVG_Q4.zip
(3c27cb509dd6d60f5ae8b434fd1ba0f4aca10d81a1b1815b077c5b52a818abfa)
and LHM433_DRA_REMAINING_Q4.zip
(6de1ccbdb646f809523fd3cbedd5143bc2a73470a1f48d0b04b13be93fa7a3a4).
For this local execution, bytes were extracted into scratch; source_manifest.json
records those local paths and the same source hashes. The delivered server
package reads the original registered locations, without moving inputs.

Replay: python -m tools.server.produce_dra_from_nhi, using those existing server
paths (or equivalent local source binding for local replay). Independent audit:
python -m tools.qualify_dra_server_output --output DRA_OUTPUT
--c2-archive docs/evidence/2026-10-19-work-c2/drainage-checkpoints.jsonl.gz
--report AUDIT_OUTPUT (each invocation on one line).

Approximation metrics retain all actual months and original activation
breakpoints; the vectorized objective was compared against its prior scalar
formula. Integrated diagnostics are trapezoidal hypothetical constant-depth
scenarios, not observed or simulated historical volume changes. Response errors
and groundwater/drainage effects still require actual model runs.
