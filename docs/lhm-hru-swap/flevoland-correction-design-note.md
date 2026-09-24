# Flevoland correction — design note

Status: **OPEN AUTHORITY / TO VERIFY**

## Physical issue

In the current LHM schematisation, some deep watercourses in Flevoland that physically cut through the confining layer are represented as if they discharge from the upper model layer. As a result, groundwater that should effectively be intercepted by those deep watercourses can first appear numerically as upward flux into the upper layer and only subsequently leave through drainage/surface-water terms.

For LWKM this intermediate routing is not necessarily the hydrological signal that should be transferred downstream.

## Consequence

The Flevoland correction is therefore potentially **not only a correction of seepage/kwel**.

If the alternative LHM calculation removes or changes this artificial routing, the associated incoming/outgoing drainage or surface-water flux terms may also need to be corrected consistently. Using corrected kwel together with uncorrected drainage terms could create an internally inconsistent water balance.

This must be verified against the actual alternative LHM run and its balance terms.

## Recommended data design

Use two directly comparable, same-schema SVAT datasets:

- `SVAT_BASE_RAW`: standard LHM result;
- `SVAT_BASE_FLEVOLAND_CORR`: same keys, columns, units and periods, but with the accepted Flevoland-corrected hydrological values for the cells where the correction applies.

The two tables must have identical SVAT keys and column definitions, so they can be diffed one-to-one.

However, the canonical authority should still preserve:

1. the raw source values;
2. the alternative/corrected source values;
3. the spatial correction mask;
4. the exact rule that selects corrected values;
5. provenance of both LHM runs.

The corrected table is therefore a **materialized scenario/view**, not an opaque manually edited replacement of the raw table.

## Required comparison

For every corrected SVAT, compare at minimum:

- kwel / upward groundwater flux;
- relevant drainage/ontwatering components;
- runoff / surface-water exchange if affected;
- storage change if affected;
- groundwater levels if affected;
- total water-balance residual.

The correction should be admitted only after the affected terms are identified and the corrected balance is physically interpretable.

## Effect accounting

The project-leader step `LHM4.3 lbn → LHM4.3 cor` should then be computed as a direct one-to-one comparison:

`SVAT_BASE_RAW[selected domain]`
versus
`SVAT_BASE_FLEVOLAND_CORR[selected domain]`.

Because schema, keys and domain are identical, the resulting delta can be attributed to the Flevoland correction rather than to selection or HRU aggregation.

## Open questions

- Which exact flux terms differ in the alternative LHM run?
- Is the correction applied only inside Flevoland, and what is the authoritative mask?
- Is the corrected kwel a direct output of the alternative run or a post-processed quantity?
- Which drainage/ontwatering terms must be replaced together with kwel?
- Does the alternative run change GHG/GLG or storage enough that these must also be taken from the corrected run?
- Can the corrected state be reproduced from a versioned transformation, or must the alternative LHM run itself remain an upstream input authority?
