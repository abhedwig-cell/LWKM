# P12 seven-to-five drainage compression design decision — 2026-10-08

Status: **DESIGN DECISION; NOT PRODUCTION ADMISSION**

## Decision

Use an explicit hydraulically screened compression policy, not a fixed nationwide five-level mapping.

1. If <=5 complete, active physical systems, do not compress.
2. Preserve H1 as its own monthly dynamic stage level.
3. Preserve PIPE as its own drain-tube level.
4. Prefer MVG+OLF within drain-only open-channel class if flux-screen passes.
5. For P/S/T evaluate S+T, P+S, P+T, and where necessary P+S+T, selecting a feasible minimum-error candidate, not simply the smallest static peil gap.
6. Never merge across infiltration-capable/drain-only classes or with PIPE; preserve source lineage and total conductance.
7. Incomplete P/S/T RIV records are excluded after stage-to-bottom fallback; missing infiltration factors count as zero without suppressing drainage conductance.
8. If no candidate meets independently justified limits, fail closed and report the HRU. Do not force a five-level representation.

## Current exceptional HRU disposition

The previously screened six HRUs:
- 3576: P+S+T candidate, ~0.028 m normalized flux error, leave MVG/OLF separate.
- 7737: P+S+T candidate, ~0.025 m normalized flux error, leave MVG/OLF separate.
- 8842: S+T best regional pair, ~0.1002 m; borderline and not admitted.
- 1178: P+S best pair, ~0.1126 m; not admitted.
- 10080: P+S best pair, ~0.1308 m; not admitted.
- 8821: S+T best pair, ~0.3229 m; no acceptable candidate established.

These are diagnostic equivalence-head errors, not realized SWAP water-balance or groundwater-response errors.

## Admission gates still required

- Recompute the entire 10,242-HRU candidate policy from the final complete-RIV source selection.
- Test true flux curves for both drainage and infiltration, seasonal transitions, and H1 dynamic stage.
- Check all SWAP method-3 parser bounds, ordering, indexed macropore-drainage lineage, and conservation.
- Qualify physical meaning of tolerance thresholds with representative SWAP sensitivity runs.
- Do not silently relax limits for the four unresolved HRUs.

The design is decided. Production admission remains open.
