# P12 SWAP level ordering authority — 2026-10-07

## Question

After seven physical LHM drainage systems are compressed to at most five SWAP
levels, does the input index/order of those SWAP levels have hydraulic meaning?

The answer is bounded by the active LWKM SWAP switches.

## SWAP source authority

Pinned SWAP5 canonical reference:

`abhedwig-cell/SWAP5@19d7ce86f71c7fa5fd3ed2c65a91dc705921f714`

Relevant SWAP 4.3.1/B1.11 source:

- `reference/swap-4.3.1/b1_11_frost_source/SWAP/drainage.f90`
  blob SHA `30e4ba432479072cee0f49b12e3e97750a308330`;
- `reference/swap-4.3.1/b1_11_frost_source/SWAP/divdra.f90`
  blob SHA `b541e48d5978b53598157d773167f0a8d651b433`.

## Method-3 total drainage flux

For `DRAMET=3`, `drainflux_basic` loops over every level independently.

For each level it obtains the time-dependent drain/open-water level, computes
head difference, and applies that level's DRARES or INFRES and SWALLO.

With LWKM's:

- `SWINTFL=0`;
- `SWTOPNRSRF=0`;

there is no special "last level = interflow" behavior.

Therefore the **total flux calculated for each drainage level** does not require
a prescribed deepest-to-shallowest or shallowest-to-deepest input order.

## SWDIVD vertical distribution

LWKM does use:

`SWDIVD=1`.

The B1.11 `divdra` routine does not simply assume the input index is the
drainage-system order. It constructs an active-system sequence `drnseq` and
sorts it by:

`HelpFl = FDisInf * Lspacing`

in descending order.

The first element of that internal sequence receives the first-order/deepest
model discharge-layer treatment, after which later orders are derived from the
cumulative discharge distribution.

## Consequence of the modern LWKM L contract

Modern LWKM authority assigns, for every active physical drainage component in
one HRU:

`L = 4 * representative-SVAT dqsat`.

Thus all active systems in the same HRU normally have the same L.

LWKM does not currently activate `SWDIVDINF=1`, so `FDisInf=1` in normal
operation.

Therefore all active systems have the same `FDisInf * Lspacing` sorting key.

The B1.11 sorting code only swaps elements when one key is strictly lower than
another. Equal keys retain the supplied order.

Qualified finding:

`EQUAL_L_DIVDRA_TIE_PRESERVES_INPUT_LEVEL_ORDER`.

## Meaning

Two statements must remain separate.

### Closed

For `DRAMET=3`, `SWINTFL=0`:
- input order does not change the independently calculated total qdrain of each
  level.

### Still open

For `SWDIVD=1` with equal L:
- input order can affect which drainage system is treated as first/second/etc.
  order in the **vertical distribution of qdrain over SWAP soil compartments**.

That vertical distribution can feed back into soil-water dynamics even while
the total drainage exchange remains unchanged.

Therefore SWAP-level ordering is **not yet production-admitted as arbitrary**.

## Current candidate

`tools/dra_level_compression.py` currently emits a deterministic candidate
ordering:

1. greater drainage depth first;
2. then medium;
3. then source lineage.

This is effectively a **deepest-first candidate**.

It is physically plausible because DIVDRA's first-order discharge layer is the
deepest/fullest discharge-layer route, but this interpretation has not yet been
qualified by a real SWAP sensitivity run.

Status:

`DEEPEST_FIRST_ORDERING_CANDIDATE_NOT_ADMITTED`.

## Required diagnostic

The 10,242-HRU DRA population diagnostic must report:

- HRUs with more than one active/compressed SWAP level;
- HRUs where all output levels share the same L and therefore enter the DIVDRA
  equal-key tie;
- the actual deepest-first level lineage for every HRU;
- HRUs requiring 7->5 compression;
- merge-cost distribution.

After population characterization, run bounded SWAP sensitivity cases for
representative HRUs, comparing at minimum:

- deepest-first;
- reverse/shallowest-first;
- one alternative deterministic lineage ordering.

Compare:
- total drainage;
- per-level drainage;
- vertical qdra distribution;
- groundwater level;
- root-zone water balance;
- final SWAP water balance.

If those differences are negligible under a preregistered tolerance, ordering
can be admitted as operationally non-sensitive. Otherwise a physically
qualified ordering rule must become production authority.

## Decision

Do not treat the current deterministic sort as final scientific authority.

Retain it as a reproducible candidate while population and SWAP sensitivity
evidence are built.
