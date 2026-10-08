# P12 DRA HRU-agnostic automation contract — 2026-10-08

Status: DESIGN REQUIREMENT; IMPLEMENTATION AND ADMISSION PENDING.

## Requirement

The seven-physical-system LHM-to-SWAP drainage pipeline MUST work with a future, changed HRU partition. The present 10,242-HRU population is a qualification fixture, not a hard-coded production domain. No HRU ID, number of HRUs, exceptional HRU shortlist, or present source-system combination may be embedded as a production special case.

## Reproducible workflow

1. Load versioned LHM source raster manifest and current HRU/SVAT membership and representative-SVAT authority. Validate spatial geometry, IDs, unique membership, coordinates, and input provenance.
2. Select valid physical RIV records cell by cell. Missing infiltration factor = 0, valid peil is retained, missing seasonal peil may fall back to corresponding valid bottom, and a still-incomplete RIV record is excluded. Record excluded cell count, conductance and reasons. No implicit default for missing bottoms or unrelated source attributes.
3. Aggregate all seven physical systems independently per current HRU, including H1 monthly stages and representative-SVAT dqsat-derived L. All aggregation is all-member, never first-member or fixed-system-index.
4. If <=5 active systems, preserve them. Otherwise enumerate hydraulically compatible partitions. H1 and PIPE are protected. Candidate P/S/T and MVG/OLF merges are evaluated using complete drainage and infiltration flux curves, with explicit versioned acceptance criteria. Preserve source lineage and conductance. Fail closed if no acceptable candidate exists.
5. Validate SWAP method-3 ranges, levels, ordering, H1 time series, indexed macropore drainage lineage and complete SWP/DRA interface.
6. Emit deterministic per-HRU DRA/SWP files, a machine-readable qualification report, and a full provenance manifest. Production admission requires zero unexplained failures. Failed HRUs remain visible and block release rather than silently disappearing.

## Incremental regeneration

Calculate per-HRU content fingerprints over sorted membership, sampled source values, relevant monthly series, representative dqsat, algorithm/configuration version, and output schema. Reuse only outputs whose complete dependency fingerprint is unchanged and previously qualified. Global configuration or algorithm changes invalidate dependent outputs. Atomic write/rename and immutable run manifests prevent partial production releases.

## Gates

- Unit/regression tests, including alternative HRU partitions and reordered memberships.
- Recompute present 10,242 HRUs and compare against reference evidence.
- Metamorphic tests: HRU ID renumbering, row reordering, HRU split/merge, changed representative SVAT, changed raster values and incremental rebuild.
- Conservation and flux-equivalence diagnostics, outlier review, fail-closed handling.
- Representative SWAP sensitivity tests before production admission.

Current design decision does not mean the complete automated production pipeline exists. No production admission granted.
