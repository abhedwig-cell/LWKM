# Flevoland correction — reconstructed working authority

Status: **KWEL-ONLY WORKING AUTHORITY**

## Scope and provenance clarification

Project-owner clarification on 28 September 2026:

- the LWKM Flevoland correction concerns a set of SVAT cells with changed **kwel**;
- the corrected values were produced by **Deltares postprocessing/editing of LHM output files**;
- they are not the result of a separate alternative LHM model run as previously hypothesized.

The exact Deltares postprocessing method/script is not yet bound. “Postprocessing/editing” is therefore the formal description used here; no unverified implementation is inferred.

## Reconstructed transformation

The bound production control distinguishes:

- original kwel: `LHM_uitvoer\filter\Kwel_1991-2020.asc`;
- Deltares-corrected/used kwel: `LHM_uitvoer\kwel_corr\Kwel_1991-2020.asc`.

The current SVAT table preserves both states as:

- `kwel_org(mm/j)`;
- `kwel(mm/j)`.

The materialized correction set is therefore reconstructed directly as:

```
flevoland_kwel_corrected = kwel != kwel_org
```

within the selected SVAT domain.

Observed current result:

- 4,677 changed SVATs;
- about 268.0 km² affected;
- bounding coordinates approximately x 138,375–197,625 m and y 475,375–538,875 m;
- area-weighted kwel over the selected domain changes from about 116.93 to 108.67 mm/y;
- delta about -8.26 mm/y;
- equivalent volume delta about -210.7 million m³/y;
- within changed cells, area-weighted mean delta about -785.9 mm/y.

## Canonical S1 → S2 semantics

For the five-stage comparison, S2 is reconstructed from S1 by preserving the same SVAT keys/domain and changing only kwel:

```
S1: kwel = kwel_org
S2: kwel = Deltares-corrected kwel
```

The pair `kwel_org` / `kwel` records the actual historical correction set and is preferable to reconstructing that set from a geographic polygon.

Do not add drainage, runoff or other hydrological changes to this LWKM transformation unless separate evidence establishes that Deltares also edited those outputs for this correction.

## Remaining provenance gap

The transformation and its output are reconstructable. The remaining upstream gap is narrower:

- which exact LHM output file(s) Deltares edited;
- exact script/tool/manual procedure;
- selection/mask used;
- formula or replacement source for corrected values;
- responsible/versioned delivery if available.

This provenance gap does not block reconstruction of the observed S1 → S2 state transition.

## QA for canonical implementation

Persist per affected SVAT:

- SVAT id;
- x/y;
- area;
- `kwel_raw_mm_y`;
- `kwel_corrected_mm_y`;
- `delta_kwel_mm_y`;
- correction source/method id when recovered.

Required checks:

1. S1 and S2 have identical SVAT keys and area;
2. only kwel changes in this transformation;
3. affected-cell count equals 4,677 for the bound current dataset;
4. national and affected-area weighted deltas reproduce the observed diagnostics;
5. raw and corrected kwel remain separately available.
