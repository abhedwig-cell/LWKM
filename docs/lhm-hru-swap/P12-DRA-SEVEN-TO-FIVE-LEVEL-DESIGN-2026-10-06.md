# DRA seven-physical-to-five-SWAP level design — 2026-10-06

## Problem statement

The current active HRU-to-SWAP drainage implementation exposes only five systems:

1. primary regional surface water;
2. secondary regional surface water;
3. tertiary regional surface water;
4. pipe drainage;
5. surface/OLF drainage.

However, the LHM433 configuration and the HRUlist2SWAP source history show seven relevant physical layer-1 drainage/surface-water components:

1. H1 main surface water;
2. primary;
3. secondary;
4. tertiary;
5. MVG / surface ditches;
6. pipe drainage;
7. OLF / overland flow.

The active five-system implementation therefore omits H1 and MVG when deriving HRU drainage resistance and depth.

This must be repaired.

## Source evidence

The supplied HRUlist2SWAP history explicitly states for v0.21:

'herziening drainage: houdt nu rekening met hoofdwaterlopen/primair sec/tert greppels buis ovl'

but the current active code later fixes:

'nusys = 5'

with:

'pri', 'sec', 'ter', 'dra', 'glk'.

The current control file likewise supplies only the five active families.

This is an internal inconsistency between stated source-history intent and the active five-system implementation.

## SWAP interface constraint

The supplied HRUlist2SWAP DRA template documents NRLEVS = [1..5] and the active producer writes NRLEVS = 5.

Therefore seven physical LHM drainage components cannot be represented one-to-one in the current SWAP drainage interface.

The correct architecture is not to omit two physical systems upstream. It is:

7 physical LHM systems -> full HRU aggregation -> explicit hydraulic compression -> <=5 SWAP levels.

## Seven physical systems

Authority: config/p12/dra-physical-systems-v2.yml.

### Open channels, infiltration-capable class

- H1;
- primary;
- secondary;
- tertiary.

### Open channels, drain-only class

- MVG / surface ditches;
- OLF / overland flow.

### Drain tube

- pipe drainage.

The pipe system remains distinct because SWAP distinguishes drain tube and open channel through SWDTYP.

## Required upstream calculation

Every physical system must first receive its own HRU-level aggregation before any reduction to SWAP levels.

For each physical system calculate independently:

- summed drainage conductance;
- summed infiltration conductance where applicable;
- DRARES;
- INFRES;
- conductance-weighted drainage bottom/depth;
- conductance-weighted summer level;
- conductance-weighted winter level;
- source lineage;
- spacing/length provenance.

No physical watercourse may disappear merely because SWAP exposes fewer levels.

## Compression principle

Compression occurs only if more than five physical systems are hydraulically active for one HRU.

If five or fewer are active, no compression is needed.

### Non-negotiable constraints

1. Drain tube is never merged with an open channel.
2. Infiltration-capable open channels are not merged with drain-only open channels.
3. Every active physical source ID must occur exactly once in the compressed lineage.
4. Total drainage conductance must be conserved.
5. Total infiltration conductance must be conserved.
6. Merged bottom and seasonal levels use drainage-conductance weighting.
7. No fixed label-based pair is assumed globally.

## Equivalent resistance

For physical systems in one merged group, the normalized conductances add in parallel.

For drainage resistance:

g_d,i = 1 / R_d,i

g_d,eq = sum(g_d,i)

R_d,eq = 1 / g_d,eq.

For infiltration resistance:

g_i,i = 1 / R_i,i

g_i,eq = sum(g_i,i)

R_i,eq = 1 / g_i,eq.

Inactive/infinite-resistance branches contribute zero conductance.

This exactly preserves the total parallel conductance represented by the merged group.

## Equivalent hydraulic levels

For drainage bottom/depth and seasonal levels use drainage-conductance weighting.

For any represented level/depth z:

z_eq = sum(g_d,i * z_i) / sum(g_d,i).

This preserves the combined linear high-head response of parallel drainage elements.

It cannot perfectly reproduce separate activation thresholds when levels differ. Therefore merges should preferentially combine hydraulically similar levels.

## Pair selection

A deterministic diagnostic compressor is implemented in tools/dra_level_compression.py.

Only compatible open-channel pairs can be merged.

The pair selected at each compression step minimizes a conductance-weighted hydraulic level variance over:

- drainage depth/bottom;
- summer level;
- winter level.

The merge cost is proportional to:

g1*g2/(g1+g2) * ((dep1-dep2)^2 + (summer1-summer2)^2 + (winter1-winter2)^2).

This is a Ward-like hydraulic clustering criterion.

It avoids a hard-coded assumption such as always merging secondary with tertiary or always merging MVG with OLF.

## Diagnostic execution

A synthetic seven-system test has been executed successfully.

Input:
- four infiltration-capable open systems;
- two drain-only open systems;
- one pipe system.

Result:
- seven active physical systems compressed to five;
- pipe remained distinct;
- every source ID remained represented exactly once;
- total drainage conductance conserved;
- total infiltration conductance conserved;
- hydraulically closest compatible pairs were selected.

The specific synthetic merge result was S + T and MVG + OLF.

This demonstrates algorithm behavior only. It is not a fixed production mapping.

## What remains unresolved

### 1. Real H1 and MVG inputs

The H1/MVG source bundle has now passed Q4 collection on the real NHI server.

Bundle:
- ZIP SHA-256: 3c27cb509dd6d60f5ae8b434fd1ba0f4aca10d81a1b1815b077c5b52a818abfa
- manifest SHA-256: 216af5086a83109abfcaa74b19c92535c354a79008ec958e0b7c0eb40fc32ebb
- 681 payload files
- 4,249,475,616 payload bytes
- zero unexplained file-identity differences after fresh extraction.

The H1 dynamic stage subset contains 676 files with filename dates from 1969-12-01 through 2026-03-01. That count equals the inclusive number of calendar months in the range, strongly indicating complete monthly coverage; exact per-month sequence confirmation still requires persistence/inspection of files.csv.

Evidence:
docs/evidence/2026-10-07/h1-mvg-q4-summary.json.

The source-recovery blocker is therefore closed. Individual member hashes, geometry checks and semantic qualification remain to be persisted before production admission.

### 2. Spacing/L semantics

The current HRUlist2SWAP implementation writes a common representative-SVAT dqsat-derived L whenever a system has non-zero length.

The physically correct L handling for compressed multi-source levels is not yet admitted.

Do not invent an equivalent spacing without a separate qualification.

### 3. Final SWAP level ordering

The diagnostic compressor returns a deterministic hydraulic ordering, but the required/optimal SWAP level ordering has not yet been independently qualified.

No production renderer change should depend on unqualified ordering semantics.

### 4. Real-population diagnostics

The compressor must be run across all 10,242 HRUs after seven physical source systems have been assembled.

Required report:
- number of active physical systems per HRU;
- number of HRUs requiring compression;
- selected merge pairs/groups per HRU;
- hydraulic merge cost distribution;
- conductance conservation checks;
- bottom/summer/winter level shifts;
- effect on DRARES/INFRES/ZBOTDR/LEVEL;
- extreme/outlier merges.

## Admission gate

The seven-to-five route is currently:

PHYSICAL_7_SYSTEMS_AUTHORITY_DEFINED_H1_MVG_Q4_RECOVERED_COMPRESSION_DIAGNOSTIC_NOT_ADMITTED.

Production admission requires:

1. qualified seven-system source inputs;
2. deterministic all-member HRU aggregation for all seven systems;
3. 10,242-HRU compression diagnostics;
4. accepted spacing/L semantics;
5. accepted SWAP level ordering;
6. regression/sensitivity showing no unacceptable hydraulic distortion;
7. complete provenance from physical source systems to every SWAP level.

## Decision

The modern workflow will no longer treat the historical five HRU drainage systems as the complete physical source model.

All seven physical layer-1 drainage/surface-water components are upstream authority.

Five levels are only a SWAP-interface representation limit.


## H1/MVG file-level audit — 2026-10-07

The uploaded Q4 ZIP was independently re-read and all 681 payload files were re-hashed against its embedded `files.csv`.

Result:
- 681/681 hashes match;
- 4,249,475,616/4,249,475,616 payload bytes accounted for;
- zero missing files;
- zero hash/size mismatches;
- all IDF headers are readable;
- all 681 files share the same 1200 x 1300, 250 m grid and national extent.

The H1 stage sequence is exactly monthly and gap-free:
- 676 unique months;
- 1969-12-01 through 2026-03-01;
- no duplicate months;
- no missing months.

Per-file NODATA must be honored:
- through 1978-10 H1 stages use -9999;
- from 1978-11 onward H1 stages use approximately 1e20;
- static H1/MVG files use approximately 1e20.

MVG source support is exact:
- 66,280 conductance cells;
- 66,280 bottom/stage cells;
- zero support mismatches.

H1 has source-support exceptions requiring an explicit policy before production:
- 296 H1 conductance cells have no explicit infiltration-factor value;
- one H1 conductance cell lacks a bottom value;
- that same cell lacks dynamic stage from 2005-01 through 2021-12;
- `PEILH_20220401` lacks stage at 15 H1 conductance cells;
- one H1 conductance cell has stage below river bottom in 436 monthly files.

These are source-data facts, not yet classified as errors in the admitted LWKM population. First determine whether the affected cells enter the production SVAT/HRU population and then reproduce or explicitly replace the LHM fallback semantics.

Evidence:
`docs/evidence/2026-10-07/h1-mvg-file-semantic-audit.json`.


## Population intersection and dynamic-level correction — 2026-10-07

### H1 source exceptions versus recovered SVAT populations

Exact coordinate searches were executed for all currently known H1 support exceptions against both recovered SVAT tables:
- `SVAT_INFO.csv`;
- `svat_info_lwkm_new.csv`.

Results:
- 296 positive-conductance H1 cells without infiltration factor: 0 coordinate matches in either table;
- 15 April-2022 H1 stage gaps: 0 coordinate matches in either table;
- the single missing-bottom / 2005-2021 stage-gap cell: 0 matches;
- the single stage-below-bottom cell: 0 matches.

Evidence:
`docs/evidence/2026-10-07/h1-source-exception-population-intersection.json`.

Interpretation:
the known H1 source irregularities are outside both recovered SVAT coordinate populations and therefore strongly appear irrelevant to the reconstructed current LWKM HRU population.

This remains bounded by W03 admission: if the formally admitted SVAT population later differs, the intersection test must be repeated.

No fallback semantics are introduced. The modern named physical-system aggregator fails closed whenever an admitted HRU member has positive conductance but lacks its required hydraulic attributes.

### Compression before SWAP-specific deactivation

The modern sequence is explicitly:

1. sample all seven physical systems;
2. aggregate all HRU members;
3. preserve every positive-conductance physical system;
4. compress hydraulically compatible systems only if active count exceeds five;
5. only then apply SWAP-level repair/deactivation rules;
6. render <=5 explicit SWAP levels.

Therefore the historical `drnres > 20000` repair is not used as an upstream physical-system deletion rule.

### Modern spacing/L

Modern spacing authority remains representative-SVAT dqsat.

For every physically active component:

`L = 4 * representative-SVAT dqsat`.

Thus all physical drainage components within one HRU have the same modern L. Compression preserves this value exactly and fails closed if conflicting non-null L values are presented.

Historical length rasters remain required only for historical replay/provenance questions, not for this modern corrected spacing contract.

### Dynamic H1 water levels

H1 is different from the other six source families because its LHM level input is a monthly `peilh_*.idf` time series.

The modern compression model therefore supports a per-level explicit level series.

Rules:
- H1 retains its monthly level profile;
- P/S/T seasonal levels are evaluated at every H1 timestamp when merged with H1;
- constant drain-only levels can likewise be evaluated at each timestamp;
- equivalent merged level at each timestamp is drainage-conductance weighted;
- dynamic profiles with inconsistent explicit date axes fail closed;
- DRA rendering writes the explicit `DATOWL/LEVEL` series rather than reducing it back to only summer/winter values.

Official SWAP method-3 input supports time-dependent open-channel `DATOWL/LEVEL` tables and at most five drainage levels. Historical SWAP 4 parameterization exposes MAOWL = 10*366 records, comfortably above the recovered 676-month H1 source sequence.

### Code state

Implemented:
- `aggregate_physical_system`: named, all-member, fail-closed physical-system aggregation;
- `repair_system_explicit`: medium-based rather than system-number-based repair;
- `render_dra_explicit`: explicit medium/infiltration semantics and dynamic level tables;
- `dra_level_compression.py`: seven-to-five hydraulic compression, source lineage, conductance conservation, representative-dqsat spacing preservation and dynamic-level-series merging.

Historical functions remain available separately for compatibility/regression.

Current status:

`SEVEN_SYSTEM_MODERN_DRA_PIPELINE_IMPLEMENTED_NOT_10242_QUALIFIED`.
