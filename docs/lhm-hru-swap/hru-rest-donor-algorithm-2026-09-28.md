# HRU rest-group donor matching algorithm — 28 September 2026

Status: **SOURCE-BOUND**

The donor relation produced inside HRU clustering after valid clusters exist is now semantically bound from the R source/documentation.

## Round 1

Targets in the rest/suspected population are matched to donors within `LDGB × lu4`.

Weighted nearest-neighbour features:

- `grondsoort2`: 250;
- `grondsoort4`: 100;
- ordered `pawn21`: 10;
- `Gt`: 0.5;
- `kwelklasse4`: 0.5;
- `GHG`: 0.01;
- `NettoKwel`: 0.01.

Subgroups with fewer than four donors continue to round 2.

## Round 2

Matching broadens to `LDGB × lu2` using the same features plus:

- `lu4` code: 250.

Subgroups with fewer than two donors remain unresolved.

## Final remainder

Targets still unresolved are grouped into new HRUs by:

- LDGB;
- lu4;
- grondsoort4;
- Gt.

Within each group, a SVAT from the largest subgroup is selected as donor (`HRUextra`).

## Distance implementation

The R helper `find_best_matches_ann()` uses RANN nearest-neighbour search. Input dimensions are multiplied by the square root of their configured weights before Euclidean nearest-neighbour matching, giving the intended weighted squared-distance influence.

## Consequence

The later `hru_cluster_donor_svat` relation is no longer an unexplained historical artifact. Its source algorithm is bound. This relation must remain distinct from the earlier 20,934 qualification marker and from `hru_representative_svat`.
