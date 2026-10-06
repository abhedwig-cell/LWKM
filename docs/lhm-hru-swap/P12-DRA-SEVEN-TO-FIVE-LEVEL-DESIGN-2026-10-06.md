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

The exact modern H1 and MVG source files must be recovered and file-qualified from the LHM input authority.

The supplied LHM INI identifies candidate source roles including H1 conductance, H1 bottom, H1 dynamic stage, H1 infiltration factor, MVG conductance and MVG bottom/stage.

Exact server bytes and hashes still need qualification.

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

PHYSICAL_7_SYSTEMS_AUTHORITY_DEFINED_COMPRESSION_DIAGNOSTIC_NOT_ADMITTED.

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
