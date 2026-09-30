# P12 STATIC04 targeted realized discriminator — HRU 7877

Status:
**TARGETED DISCRIMINATOR IDENTIFIED; REALIZED DRA BYTE ACCESS PENDING**

## Why HRU 7877 matters

The supplied 49-run validation set explicitly contains HRU 7877.

Repository validation notes:
- HRU 7877 has 28 members;
- 27 donor-source members;
- 1 matched target member.

The full source-side STATIC04 comparison gives:

- legacy majority-BFE dqsat: **18 cm**;
- representative-SVAT dqsat: **17 cm**.

Therefore HRU 7877 is a true discriminator between the two dqsat authorities.

For every active drainage system with positive source length:

- legacy predicts `L = 72 cm`;
- schema-first representative-SVAT authority predicts `L = 68 cm`.

Fallback `L = 100` remains non-discriminating for a system with zero total source length.

## Minimal realized evidence needed

A single raw realized file:

`7877.dra`

is sufficient to classify the executable's dqsat authority for any active system in that file:

- realized `L = 72` -> evidence for legacy majority-BFE dqsat;
- realized `L = 68` -> evidence for representative-SVAT dqsat;
- another active-system L -> unexplained/provenance mismatch;
- only fallback L=100 systems -> this HRU/file remains non-discriminating operationally.

This does not replace the full 49-run DRA admission gate. It narrows the STATIC04 executable-discrimination evidence requirement from the complete archive to one known discriminating run when only authority classification is at issue.

## Important boundary

Do not infer the representative dqsat from realized L. Both source-side hypotheses were reconstructed independently before consulting the realized oracle.

Do not use the historical Runs intermediate as a substitute unless its exact executable/run provenance is demonstrated to match the supplied realized 49-run set.

## Current access state

`run_files.zip` is present in Project Files but raw bytes remain unauthorized for materialization. No loose `7877.dra` object is currently exposed separately.

Classification:

**STATIC04_REALIZED_TARGET_HRU_7877_READY**
