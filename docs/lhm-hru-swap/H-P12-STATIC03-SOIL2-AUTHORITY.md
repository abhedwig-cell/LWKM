# H-P12-STATIC03 — soil2 authority resolution

## Resolved semantics

Earlier workflow reconstruction established soil2 / grondsoort2 as a deterministic lookup-derived soil class, not an independent HRU decision.

Realized hierarchy:
  bodem370 -> BOFEK79 -> PAWN21 -> grondsoort4 -> grondsoort2

soil2 is the final coarse crop-soil class (sand/loam versus clay/peat).

For realized source mappings, each present bodem370 code had one deterministic realized classification combination. The realized SVAT_INFO mapping is authority for historical reconstruction; earlier audit found 10 bodem370->BOFEK differences versus Bodem370_2_bofek2020.csv, so do not silently replace realized lookup provenance with that external table.

## Legacy hrulist2SWAP behavior

The Fortran nevertheless recomputes:
  soil2_maj = MAJORITY(member soil2)
then combines it with the later representative land use:
  lu2crop(soil2_maj, representative_lgn)

This is a second reduction after soil classification has already been established upstream.

## Modern authority

For the schema-first production path:
1. take Piet's authoritative representative soil / representative SVAT;
2. resolve its soil classification through the preserved authoritative lookup chain;
3. derive representative_soil2 / grondsoort2;
4. combine that with representative_landuse for crop lookup.

Do not recompute soil2 by HRU member majority in the production path.

Member-majority soil2 may be retained as QA and legacy-compatibility diagnostic only.

## Classification

LEGACY_AUTHORITY_REDUCTION_SUPERSEDED_BY_SCHEMA_FIRST_LOOKUP.

Production impact relative to realized historical SWP remains to be quantified where representative-derived soil2 differs from member-majority soil2.
