# P12 missing seasonal stage fallback — 2026-10-08

Status: OWNER-CONFIRMED POLICY; IMPLEMENTATION/QUALIFICATION PENDING.

On 2026-10-08 the domain owner confirmed: when a seasonal water level is missing, the watercourse bottom may be used as its value.

Apply this **per active source cell and per season**, before HRU conductance-weighted aggregation. Preserve valid levels and preserve drainage conductance. Do not interpret missing stage as inactive drainage.

For P and S, use the corresponding seasonal LHM RIV-package bottom (P/S BODH_*Z/W). Do not silently use historical J bottoms instead.

For T, the current LHM433 INI binds seasonal rbot to the same PEIL_T1Z/W grid. Consequently if that source cell is missing in PEIL, the package-bound bottom is also missing and this rule cannot resolve the gap by itself. Fail closed and report unresolved source cell/HRU. A separately qualified alternative bottom authority would be required.

If the corresponding bottom is missing, fail closed. Count stage substitutions and unresolved cells/HRUs separately. Do not change missing-infiltration-factor=0 policy or infer any other fallback.

Next gates: implement in the seven-system runner, add targeted tests, replay the 15 stage-blocked HRUs, quantify residual unresolved T cells, and rerun protected five-level compression plus flux curves. No production admission yet.
