# P12 missing infiltration factor policy — 2026-10-08

Status: USER-CONFIRMED SOURCE SEMANTICS; PRODUCTION ADMISSION STILL PENDING

The LHM domain owner explicitly confirmed on 2026-10-08: **missing infiltration factor = 0**.

Scope: positive-conductance P/S/T river cells with a missing infiltration-factor raster value. Preserve positive drainage conductance. For those cells, infiltration contribution is zero: `G_inf = G_drain * 0 = 0`. This does **not** deactivate the physical drainage system.

This supersedes the diagnostic-only fail-closed interpretation for this specific missing-factor condition. It does not authorize zero substitution for missing stage, bottom, conductance, geometry or other source attributes.

The earlier fallback 184 screening used zero for missing infiltration factors. Under this newly confirmed semantic rule, its previously reported 116 candidate-passing HRUs can be treated as *screening candidates* again; 68 HRUs still fail the provisional five-level thresholds. Neither number is a full physical flux validation or production admission.

Implementation requirements:
1. Record missing-factor masks/counts separately from valid explicit zeros.
2. Apply zero only to infiltration factors; do not alter drainage conductance.
3. Add tests for positive drainage conductance plus missing infiltration factor.
4. Re-evaluate 68 unresolved HRUs and the full flux curves under documented tolerances.
5. Maintain H1 and PIPE protection and preserve source lineage.

No DRA production admission is granted by this note.
