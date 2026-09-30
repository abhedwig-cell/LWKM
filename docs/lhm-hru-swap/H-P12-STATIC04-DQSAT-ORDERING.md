# H-P12-STATIC04 — dqsat representative-soil ordering defect

## Source finding

Legacy source:
1. computes `bfe_maj` as member-raster majority;
2. selects dqsat values only from members with `bfe == bfe_maj`;
3. sets `dqsat_maj = MAJORITYR4(selected dqsat)`;
4. later, when Piet HRU schema exists, overrides the final representative BFE/profile;
5. does not recompute `dqsat_maj`.

Thus a final HRU can combine:
- representative soil/profile authority;
- dqsat derived from a different legacy majority-soil population.

Classification:
**DEFECT_CONFIRMED_AUTHORITY_ORDERING**.

## Downstream impact

`dqsat_maj` is:
- written to the historical Runs intermediate as field `dqsat`;
- used in DRA as `L = 4 * dqsat_maj` whenever the system has positive source length.

A mismatch therefore changes drainage spacing/geometry as well as the typed run record.

## Independent run-2000 oracle

Available raw oracle:
- `2000.dra`;
- SHA-256 `85dff23754d138b12e3084e5c06c6ad3eb77880c64d7a24f85aa48aae4acd15e`.

Recovered historical `Datamodel_10242.xlsx`:
- SHA-256 `5a4e68cb958cb8187639db7750e957c509caf67f81b5b11096c929ca796244d8`;
- row for run 2000 has `dqsat = 20`.

Realized DRA:
- L1 = 100, the source fallback value and therefore non-discriminating;
- L2 = 80;
- L3 = 80;
- L4 = 80;
- L5 = 80.

For systems 2-5:
`L / 4 = 20`.

Therefore:
**realized DRA dqsat_used = Runs.dqsat = 20 for run 2000**.

This independently confirms propagation from the historical dqsat intermediate into DRA geometry.

It does not establish whether 20 came from:
A. the defective legacy majority-BFE population;
B. the intended representative-SVAT semantics.

Run 2000 is therefore useful but non-discriminating for the authority correction itself.

## Falsified shortcut: dqsat from representative bodem_id alone

The recovered 10,242-run historical datamodel allows a direct test of a possible fallback:
“derive dqsat deterministically from final representative `Runs.bodem_id`.”

Result:
- Runs rows: 10,242;
- distinct occurring `bodem_id` values: 337;
- bodem codes with exactly one observed dqsat value: 88;
- bodem codes with multiple observed dqsat values: **249**;
- maximum number of distinct dqsat values for one bodem code: **15**;
- observed dqsat values span 0 and 2 through 20 cm.

Examples:
- bodem 79 occurs with dqsat 0, 3, 4, 5, 6, 9, 10, 12, 14, 16, 17, 18, 19 and 20;
- bodem 131 occurs with 4, 5, 6, 10, 12, 13, 14, 18 and 20;
- bodem 253 occurs with 0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 19 and 20.

Therefore:
**REPRESENTATIVE_BODEM_ONLY_DQSAT_FALLBACK_FALSIFIED**.

A deterministic fallback based only on the representative soil identity would collapse real within-soil dqsat variation and is not admissible.

## Correct schema-first semantics

The production hierarchy is now narrowed to:

1. use dqsat from the explicit representative SVAT selected by the authoritative HRU schema, provided the value is valid;
2. only if representative-SVAT dqsat is unavailable, use a separately qualified rule that contains more information than `bodem_id` alone.

Do not use:
- the legacy majority-BFE member reduction;
- a new HRU member-majority reduction;
- a simple `bodem_id -> dqsat` lookup.

The remaining primary authority question is therefore no longer “soil or SVAT?”. The representative-SVAT route is the only currently defensible direct candidate.

## Remaining oracle gate

For each realized HRU/system with `L != 100`:
`realized dqsat_used = L / 4`.

Compare against:
- legacy majority-BFE dqsat;
- representative-SVAT dqsat.

The needed Project raster is located:
- `grensvlak_NHIWQ_v2_fill.asc`, 3,521,406 bytes.

Its raw backing bytes are still not authorized for materialization.

The 49-run DRA oracle set is also not currently raw-readable in this Library surface.

Classification of remaining work:
**BLOCKER_RAW_REPRESENTATIVE_SVAT_DQSAT_AND_DISCRIMINATING_DRA_ORACLES**.

Do not infer representative dqsat from realized L values. That would make the authority test circular.
