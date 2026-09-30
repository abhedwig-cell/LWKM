# H-P12-STATIC02 — representative-landuse override ordering defect

## Source finding

Legacy source computes from raster-member majority `lgn_maj`:
- `swetr`: `lgn_maj < 7 -> 0`, otherwise 1;
- `isnatuur`: `10 < lgn_maj < 21` and `lgn_maj != 18`.

Later, when `HRU2SVAT_REPR_CSV` exists, source overrides the final land-use identity with Piet's representative HRU schema without recomputing those flags.

Classification at source level:
**DEFECT_CONFIRMED_AUTHORITY_ORDERING**.

## 10,242-run SWETR impact audit

The recovered current datamodel contains the final representative land-use field in `Runs.lu_id` and the legacy-emitted `Runs.SWETR`.

Source:
- `Datamodel_10242.sqlite`
- SHA-256 `4b697e7f806d0e6f0c345b92bb78c456238c3af5634559a7e2f7edd4171183bb`.

Audit rule for schema-first SWETR:
- representative `lu_id < 7` -> SWETR 0;
- representative `lu_id >= 7` -> SWETR 1.

Result over all 10,242 Runs rows:
- SWETR 0 / schema-first 0: **7,162**;
- SWETR 1 / schema-first 1: **3,080**;
- mismatch: **0 / 10,242**.

Therefore the source ordering defect has **no realized production impact on SWETR in the current 10,242-run datamodel**.

This is a useful negative result. It means the modern schema-first rule can replace the defective control flow without producing a SWETR difference for the current production population.

Classification for SWETR:
**DEFECT_CONFIRMED_BUT_CURRENT_POPULATION_NON_DISCRIMINATING**.

The audit is reproducible through:
`tools/audit_p12_static_authority.py`.

## Nature / DRA system 4

The same zero-impact conclusion cannot be extended automatically to `isnatuur`.

Representative-landuse nature rule:
`10 < lu_id < 21 and lu_id != 18`.

The current datamodel contains **2,825** runs whose final representative land use meets that nature criterion, but the legacy pre-override `isnatuur` value is not persisted in Runs.

Therefore DRA system-4 suppression remains a realized-output question:
- compare raw DRARES4 with the >20000 independent shutdown condition;
- then compare realized system-4 state against legacy-majority and representative-landuse hypotheses.

The available raw run-2000 oracle is non-discriminating:
- representative `lu_id = 1`, so schema-first `isnatuur = false`;
- realized `DRARES4 = 17040`, not independently disabled by the >20000 rule;
- realized system 4 remains active, consistent with `isnatuur = false`.

A 49-run nature conclusion still requires the missing realized DRA set or equivalent raw oracle access.

## Production rule

Modern production must derive all land-use-dependent fields from the authoritative representative land use:
- SWETR;
- nature flag;
- crop mapping and related switches.

Member-majority land use may remain only as QA/legacy diagnostic.
