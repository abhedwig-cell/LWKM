# P12 SWAP drainage level-table source authority — 2026-10-07

## Purpose

This note binds the modern LWKM seven-to-five drainage design to the actual
SWAP 4.3.1/B1.11 drainage input semantics.

It answers two interface questions:

1. can one SWAP drainage level carry a time-dependent H1 water-level series?
2. is the number of drainage levels bounded independently from the number of
   water-level dates?

## Source authority

Repository:

`abhedwig-cell/SWAP5`

Pinned canonical commit inspected:

`19d7ce86f71c7fa5fd3ed2c65a91dc705921f714`

Reference source:

`reference/swap-4.3.1/b1_11_frost_source/SWAP/drainage.f90`

Blob SHA:

`30e4ba432479072cee0f49b12e3e97750a308330`

Companion module:

`reference/swap-4.3.1/b1_11_frost_source/SWAP/MOD_drainage.f90`

Blob SHA:

`716df027e43c37f62718ff080bbd8dff938b9307`.

## Input parser finding

For drainage method 3, the source reads:

- `NRLEVS` as the number of drainage levels;
- for each level:
  - DRARES;
  - INFRES;
  - SWALLO;
  - L;
  - ZBOTDR;
  - SWDTYP;
  - DATOWL;
  - LEVEL.

The parser invokes a time-array reader for each `DATOWL<n>` table and a
numeric-array reader for its matching `LEVEL<n>` values.

The values are stored in `owltab(level,...)` and the number of water-level
records is stored separately in `nowltab(level)`.

Therefore:

`NUMBER_OF_DRAINAGE_LEVELS != NUMBER_OF_WATER_LEVEL_DATES`.

A single drainage level may legitimately contain many water-level dates.

## Runtime finding

The basic drainage runtime evaluates the prescribed open-water-level table
through `afgen` using current model time `t1900`.

Therefore the water level of one SWAP drainage level is a time-dependent
runtime quantity, not a single static level forced by the DRA interface.

This directly supports retaining the qualified LHM H1 monthly
`peilh_*.idf` dynamics when the physical H1 system is mapped into a SWAP
level.

## Consequence for LWKM

The modern representation may use:

```text
one physical/compressed SWAP level
  -> one DRARES / INFRES / L / ZBOTDR / SWDTYP
  -> many DATOWL / LEVEL records
```

Thus the SWAP five-level limit does **not** require reducing H1 monthly dynamics
to only a summer and winter value.

If H1 is merged with another compatible open-channel physical system, the
equivalent level may be calculated at every retained timestamp using the
already qualified conductance-weighted merge rule.

## Source-bounded claim

Qualified:

`MONTHLY_H1_LEVEL_SERIES_IS_COMPATIBLE_WITH_SWAP_METHOD3_LEVEL_TABLE_INTERFACE`.

Not established by this note:

- the exact interpolation/extrapolation rule of `afgen` outside the supplied
  date range;
- whether a terminal 2022-01-01 H1 record is preferable for a simulation ending
  2021-12-31;
- final production ordering of compressed SWAP levels.

Those remain separate qualification questions.

## Current rendering rule

`tools/generate_dra.py::render_dra_explicit` supports an explicit level series
and serializes deterministic English month tokens.

For the current historical production interval the population diagnostic
defaults to H1 records from 1971-01-01 through 2021-12-01.

Before final production admission, the end-of-table behavior must either:
- be source-qualified for `afgen`; or
- be made unambiguous by providing a qualified terminal record beyond the
  simulation end.
