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

Recovered historical `Datamodel_10242.xlsx` row for run 2000:
- `dqsat = 20`.

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

It does not yet establish whether 20 came from:
A. the defective legacy majority-BFE population;
B. the intended representative-soil/SVAT semantics.

Run 2000 is therefore useful but non-discriminating for the authority correction itself.

## Correct schema-first semantics

Resolve representative soil/BFE first.

Then derive dqsat from explicit representative authority.

Preferred candidate hierarchy:
1. representative SVAT dqsat when that SVAT is the explicit HRU representative and the value is valid;
2. otherwise a separately qualified deterministic representative-soil rule.

Do not use a fresh HRU member-majority reduction merely to reproduce the legacy ordering.

The exact fallback between options 1 and 2 remains to be bound from raw source evidence.

## Remaining oracle gate

The intended discriminating gate remains:

For each realized HRU/system with `L != 100`:
`realized dqsat_used = L / 4`.

Compare against:
- legacy majority-BFE dqsat;
- representative-SVAT/representative-soil dqsat.

The needed Project raster is located:
- `grensvlak_NHIWQ_v2_fill.asc`, 3,521,406 bytes.

Its raw backing bytes are currently not authorized for materialization.

The 49-run DRA oracle set is also not currently raw-readable in this Library surface.

Classification of remaining work:
**BLOCKER_RAW_DQSAT_RASTER_AND_DISCRIMINATING_DRA_ORACLES**.

Do not infer the missing dqsat source from realized L values. That would make the authority test circular.
