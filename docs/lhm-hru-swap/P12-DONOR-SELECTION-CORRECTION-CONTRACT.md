# P12 donor-selection correction contract

The correction must use clustering semantics, not the historical variable name isverdacht.

## Membership classes

DONOR_SOURCE
  svat_orig == svat_donor.
  This is an actual donor/source member and is eligible for direct hydrological aggregation.

MATCHED_TARGET
  svat_orig != svat_donor and label corresponds to a donor-matched target ("Toegevoegd").
  Its donor attributes represent the HRU assignment. Do not treat the target as the preferred source merely because it was added to the HRU.

RESTGROUP_DONOR
  label Restgroep and svat_orig == svat_donor.
  This member is the chosen donor/source within a newly created remainder HRU.

RESTGROUP_TARGET
  label Restgroep and svat_orig != svat_donor.
  This member belongs to the new remainder HRU but is represented by its Restgroep donor.

## Candidate water-balance membership

Use DONOR_SOURCE + RESTGROUP_DONOR:
  selected = (svat_orig == svat_donor)

This single equality naturally handles ordinary clusters, matched targets and new restgroup HRUs without label-specific hydrological branching.

## Why labels remain stored

Labels are provenance and QA, not the selection algorithm. The equality is the semantic relation; label classes explain how that relation arose.

## Legacy compatibility

Historical selection remains reproducible as a named legacy mode:
  selected = (svat_orig != svat_donor)
  fallback all if none.

Corrected mode must never silently fall back to all. If an HRU has zero donor-equal members, fail validation because that contradicts the clustering contract and indicates corrupt/incompatible input.
