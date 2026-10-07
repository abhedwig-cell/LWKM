# P12 DRA protected merge-policy population diagnostic — 2026-10-07

Status: **IMPLEMENTED; POPULATION EXECUTION PENDING; NOT ADMISSION**

## Motivation

The seven-physical-system population preflight shows that 6,019 of 10,242 HRUs
have more than five active drainage systems. Compression is therefore a central
production concern rather than an edge case.

A purely label-independent minimum-cost compressor remains useful as a neutral
diagnostic, but two source semantics deserve explicit protection/review:

- **H1** has a qualified monthly dynamic stage series and should not silently be
  collapsed into a seasonal P/S/T level merely because a static cost is low.
- **PIPE** is a drain-tube level and remains physically distinct from open
  channels.

Two physically motivated candidate merge families are therefore reviewed
explicitly:

1. **MVG + OLF**, both drain-only open channels;
2. **S + T**, both infiltration-capable regional open channels with seasonal
   stage semantics.

No fixed merge is admitted in advance.

## Tool

`tools/diagnose_dra_merge_policy_10242.py`

Inputs:
- authoritative `export_svat_HRU_NRU_10242.csv`;
- Q4 `LHM433_H1_MVG_Q4.zip`;
- Q4 `LHM433_DRA_REMAINING_Q4.zip`.

Representative dqsat is deliberately not required because all physical systems
inside one HRU share the same modern spacing authority and spacing does not
choose between these candidate pairs.

## Metrics

### MVG + OLF

For every HRU where both systems have positive conductance:
- MVG fraction of total MVG+OLF drainage conductance;
- separation of their conductance-weighted physical levels;
- normalized maximum threshold-collapse flux error.

For two parallel drain-only systems with conductance fraction `f` and source
level separation `dz`, the normalized maximum threshold-collapse error is
reported as:

`f * (1-f) * |dz|`

with units of equivalent head. This is zero when one branch is negligible or
when the source levels coincide.

### S + T

For every HRU where both systems are active:
- S fraction of S+T drainage conductance;
- maximum summer/winter source-level separation;
- mean seasonal bottom separation;
- maximum gap between the drainage-conductance-weighted equivalent level and
  infiltration-conductance-weighted equivalent level.

The final metric is important because one SWAP method-3 level exposes one water
level to both DRARES and INFRES. A non-zero gap is therefore irreducible
representation tension for a one-level S+T merge.

## Required review

Report p50/p90/p95/p99/max and inspect the bad tail, especially within:
- all HRUs where each candidate pair is active;
- the 6,019 compression-required HRUs;
- the 2,066 seven-active-system HRUs.

A later revision should join the already generated activity preflight to emit
those two compression-specific subsets directly.

## Candidate architecture under review

When all seven physical systems are active, the physically interpretable target
is:

`H1 | P | S+T | PIPE | MVG+OLF`

but only if population evidence supports both candidate merges.

H1 and PIPE are protected semantic levels. P remains independent unless a
separately qualified fallback is needed.

## Admission rule

Do not replace the generic compressor with a fixed merge map until:
- population quantiles are available;
- outliers are inspected;
- acceptance thresholds are justified hydrologically;
- the policy has zero prohibited class/medium merges;
- conductance conservation and SWAP interface gates still pass.

Current classification:
**PROTECTED_MERGE_POLICY_DIAGNOSTIC_IMPLEMENTED_NOT_ADMITTED**.
