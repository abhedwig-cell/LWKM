# P12 DRA level-ordering resolution — 2026-10-07

## Question

After seven physical LHM drainage/surface-water systems are reduced to at most
five SWAP drainage levels, does the serialized SWAP level number itself carry
ordinary drainage physics that constrains the ordering?

## Source authority inspected

SWAP 4.3.1 B1.11 source in repository `abhedwig-cell/SWAP5`,
branch `integration/f-ci-canonical`:

- `reference/swap-4.3.1/b1_11_frost_source/SWAP/drainage.f90`
- `reference/swap-4.3.1/b1_11_frost_source/SWAP/divdra.f90`

LWKM supplied producer source:

- `hrulist2SWAP.f90`

## DRAMET=3 flux semantics

For basic drainage method 3 SWAP loops over `lev = 1..NRLEVS`.

For each level it independently:
- interpolates that level's `DATOWL/LEVEL`;
- applies that level's `ZBOTDR`;
- calculates head difference;
- uses that level's `DRARES` or `INFRES`;
- applies that level's `SWALLO` and `SWDTYP`.

The ordinary total drainage exchange is then the sum of the level fluxes.

No adjacent-level calculation (`lev-1`, `lev+1`) is used for ordinary
DRAMET=3 exchange.

## SWDIVD vertical-distribution semantics

LWKM writes `SWDIVD = 1`, so `DIVDRA` was inspected separately.

`DIVDRA` does not assume that the input level number is already the hydraulic
order. It constructs an internal `drnseq` over active systems and sorts that
sequence by:

`FDisInf(level) * Lspacing(level)`.

The subsequent model-discharge-layer construction uses that internally sorted
sequence.

Therefore serialized order is not the ordinary ordering authority for the
vertical drainage distribution either.

For the modern LWKM contract all active physical systems within one HRU use the
same representative-SVAT spacing:

`L = 4 * representative-SVAT dqsat`.

Where `FDisInf` is also equal, DIVDRA may retain the supplied order as a tie.
This can affect assignment of **individual per-level** fluxes to model
compartments, although the input-level fluxes themselves and total drainage
exchange remain separately conserved. Therefore deterministic serialization is
still required; arbitrary input ordering is not acceptable.

Modern LWKM uses deterministic output ordering:

1. deeper drainage bottom/depth first;
2. then medium;
3. then canonical source lineage.

Compression merge ties are independently broken by canonical source lineage,
not caller input order.

This gives deterministic behavior for equal DIVDRA ordering keys.

## Explicit index-sensitive exceptions

Two SWAP mechanisms give a special meaning to a drainage level index.

### Interflow

When `SWINTFL = 1`, SWAP treats `lev == NRLEVS` specially as the highest
interflow level.

The LWKM DRA producer writes:

`SWINTFL = 0`.

Therefore this special last-level semantic is inactive for the current LWKM DRA
contract.

### Rapid macropore drainage

When both:
- `SWMACRO = 1`; and
- `SWDRRAP = 1`,

SWAP uses `NUMLEVRAPDRA` as an explicit drainage-level index to derive the
rapid-drainage base.

This is a coupling from the SWP/macropore configuration into the DRA level
number.

The current Datamodel_10242 does not expose `SWMACRO`, `SWDRRAP` or
`NUMLEVRAPDRA` as case-dependent fields, but absence from the datamodel alone
does not prove that the global historical/current SWP template disables the
feature.

Therefore this remains a W10/W11 package gate.

## Qualified W07 decision

For the current W07 seven-system diagnostic and modern ordinary drainage
contract:

`DRA_LEVEL_ORDERING_CONDITIONALLY_QUALIFIED`.

Conditions:
- `DRAMET = 3`;
- `SWINTFL = 0`;
- no unbound indexed rapid-macropore drainage semantics may be active.

Under those conditions, the deterministic modern ordering is admissible for the
W07 diagnostic. No physical watercourse identity is encoded solely by the
numeric SWAP level number.

## W10/W11 fail-closed rule

Before a generated DRA is admitted into a complete SWP run package:

- if `SWMACRO = 0`, no macropore level-index binding is required;
- if `SWMACRO = 1` and `SWDRRAP = 0`, no rapid-drainage level-index binding
  is required;
- if `SWMACRO = 1` and `SWDRRAP = 1`, `NUMLEVRAPDRA` must be explicitly
  bound to the intended physical/compressed source lineage **after**
  seven-to-five compression;
- if that lineage cannot be resolved unambiguously, package assembly must fail.

A hard-coded historical number such as `NUMLEVRAPDRA=4` must never be assumed
to still identify pipe drainage after dynamic seven-to-five compression.

## Consequence

Final SWAP level ordering is no longer a blocker for the 10,242-HRU W07
compression diagnostic.

The remaining W07 blockers are:
1. Q4 qualification of P/S/T/PIPE/OLF + AHN source bundle;
2. execution of the 10,242-HRU diagnostic;
3. evaluation of compression frequency/costs and P/S/T bottom-authority
   differences;
4. regression/sensitivity acceptance.

The macropore indexed-level question moves to the complete SWP/package
qualification gate.
