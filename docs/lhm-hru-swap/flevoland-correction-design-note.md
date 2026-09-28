# Flevoland correction — reconstructed working authority

Status: **KWEL-ONLY WORKING AUTHORITY**

## Scope clarification

Project-owner clarification on 28 September 2026: in the LWKM preprocessing chain under reconstruction, the Flevoland correction concerns a set of SVAT cells with changed **kwel**. It should therefore not be expanded into a drainage or surface-water correction unless separate source evidence later proves such an additional transformation.

This supersedes the earlier speculative requirement in this note that coupled drainage terms had to be part of the LWKM Flevoland correction.

## Reconstructed transformation

The bound production control distinguishes:

- original kwel: `LHM_uitvoer\filter\Kwel_1991-2020.asc`;
- corrected/used kwel: `LHM_uitvoer\kwel_corr\Kwel_1991-2020.asc`.

The current SVAT table preserves both states as:

- `kwel_org(mm/j)`;
- `kwel(mm/j)`.

Therefore the materialized correction mask can be reconstructed directly as:

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

For the five-stage comparison, S2 can now be reconstructed from S1 by preserving the same SVAT keys/domain and replacing only the kwel state for the observed correction set:

```
S1: kwel = kwel_org
S2: kwel = kwel
```

All other variables remain unchanged for this specific LWKM transformation unless later producer evidence demonstrates otherwise.

The pair `kwel_org` / `kwel` is preferable to inferring Flevoland from a geographic polygon: it records the actual cells on which the historical correction acts.

## Remaining provenance gap

The downstream transformation is reconstructable. What is not yet fully bound is the upstream producer of the corrected `Kwel_1991-2020.asc`: exact alternative LHM run, producer script and/or source manifest.

That gap affects provenance of the corrected values, but no longer blocks reconstructing the observed S1 → S2 transformation itself.

## QA for canonical implementation

A modern implementation should persist per affected SVAT:

- SVAT id;
- x/y;
- area;
- `kwel_raw_mm_y`;
- `kwel_corrected_mm_y`;
- `delta_kwel_mm_y`;
- correction rule/source id.

Required checks:

1. S1 and S2 have identical SVAT keys and area;
2. only kwel changes in this transformation;
3. affected-cell count equals 4,677 for the bound current dataset;
4. national and affected-area weighted deltas reproduce the observed diagnostics;
5. raw and corrected kwel remain separately available.
