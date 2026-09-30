# H-P12-STATIC02 — representative-landuse override ordering defect

## Finding

Legacy source computes from raster-member majority lgn_maj:
- swetr:
    lgn_maj < 7 -> 0
    else -> 1
- isnatuur:
    10 < lgn_maj < 21 and lgn_maj != 18

Later, when HRU2SVAT_REPR_CSV exists, source overrides:
  lgn_maj = lgn(svat_repr)
using Piet's authoritative representative HRU schema.

It does NOT recompute swetr or isnatuur afterwards.

## Consequences

The final HRU can therefore contain:
- representative land use from Piet;
- SWETR derived from the earlier raster-member majority;
- DRA system-4 nature suppression derived from the earlier raster-member majority;
- crop mapping later indexed using the overridden representative lgn_maj.

This violates single-authority semantics and can make SWP/DRA internally inconsistent.

## Classification

DEFECT_CONFIRMED_AUTHORITY_ORDERING at source-code level.

Realized production impact is not yet quantified. It occurs only where:
  raster-majority landuse classification crosses a swetr or nature boundary relative to Piet's representative land use.

## Correct production semantics

Resolve authoritative HRURepresentation first.
Then derive all land-use-dependent flags from representative_landuse:
- swetr
- isnatuur
- crop mapping / related switches

Member-majority land use remains QA/fallback only.

## Required impact audit

Across all 10,242 HRUs compare:
- legacy majority lgn vs representative lgn;
- swetr legacy vs representative-derived;
- isnatuur legacy vs representative-derived.

For 49 realized runs compare:
- SWP SWETR;
- DRA system 4 enabled/disabled state;
against both hypotheses to determine generating executable behavior.

Do not alter unrelated DRA aggregation.
