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


## Remaining five-source Q4 collection — 2026-10-07

A second real-server collector is now prepared:

`tools/server/lwkm_collect_dra_remaining.ps1`.

It collects and Q4-verifies the remaining modern seven-system source families:
- primary conductance, infiltration factor, level and current-HRU bottom;
- secondary conductance, infiltration factor, level and current-HRU bottom;
- tertiary conductance, infiltration factor, level and current-HRU bottom;
- pipe conductance and bottom/stage;
- OLF conductance and bottom/stage;
- authoritative LHM MetaSWAP AHN ground level in centimetres.

The bundle also deliberately includes LHM-package seasonal P/S bottom grids separately from the current HRU DRA steady-state P/S/T bottom grids.

Reason:
the LHM INI package semantics and current HRU DRA control do not use exactly the same bottom source definitions. No modern production choice is made until those candidates are compared on the admitted LWKM support.

This collector follows the same Q2/Q4 byte-identity pattern as the H1/MVG collector:
source hash -> staged copy hash -> ZIP -> fresh extraction -> payload rehash.


## Level-ordering closure — 2026-10-07

Final W07 ordering is conditionally qualified in:

`docs/lhm-hru-swap/P12-DRA-LEVEL-ORDERING-RESOLUTION-2026-10-07.md`.

The SWAP 4.3.1 DIVDRA implementation was included in this review. DIVDRA builds
its own active-system order from `FDisInf * Lspacing`; serialized level order
is not assumed to be the hydraulic order.

Modern compression uses deterministic serialization and canonical lineage
tie-breaks.

The only remaining explicit drainage-level-index coupling is rapid macropore
drainage via `NUMLEVRAPDRA`. This is guarded at package level by
`tools/dra_package_guard.py` and is a W10/W11 concern rather than a W07
compression blocker.

## P/S/T bottom-authority diagnostic

The real LHM package and the historical HRU DRA control do not use identical
river-bottom definitions.

The 10,242 diagnostic now compares all three regional river systems:

- P: current-HRU `BODH_P1J` versus LHM package `BODH_P1Z/W`;
- S: current-HRU `BODH_S1J` versus LHM package `BODH_S1Z/W`;
- T: current-HRU `BODH_T1J` versus the LHM package's explicit use of
  `PEIL_T1Z/W` as rbot.

No modern bottom authority is selected until this comparison is measured on the
full admitted population.


## H1 time-table boundary semantics — 2026-10-07

The modern diagnostic period is aligned to the historical HRU/SWAP control:

- simulation start: 1971-01-01;
- simulation end: 2021-12-31;
- H1 source table used by the diagnostic: 1971-01-01 through 2021-12-01;
- required H1 records in that selected range: 612 consecutive monthly records.

The diagnostic now fails closed if that selected monthly sequence has any
missing or extra month.

SWAP/TTUTIL time-table semantics are:
- linear interpolation between specified time records;
- outside the specified table range, use the closest specified value.

Therefore the 2021-12-01 H1 value remains valid through 2021-12-31 when it is
the final table record. No synthetic 2022-01-01 boundary record is required by
the SWAP table reader.

This is a SWAP serialization/interpolation contract. Whether a later scientific
mapping should represent LHM monthly stages as linear or stepwise forcing is a
separate model-mapping decision and must not be changed silently.


## Drainage versus infiltration equivalent-level tension — 2026-10-07

Exact parallel conductance conservation is necessary but is not, by itself,
sufficient to prove that a compressed infiltration-capable SWAP level exactly
reproduces both branches of the two-source flux relation.

One SWAP method-3 level has one shared prescribed water level, while drainage
uses DRARES and infiltration uses INFRES.

For two physical systems A and B:

- the drainage-equivalent level is weighted by drainage conductance;
- the infiltration-equivalent level is weighted by infiltration conductance.

If the two physical systems have different infiltration/drainage conductance
ratios, those two equivalent levels need not coincide.

The diagnostic quantity is therefore:

`max_drainage_infiltration_level_gap_m`

defined as the maximum absolute difference, over all retained level timestamps,
between:

1. the drainage-conductance-weighted equivalent level; and
2. the infiltration-conductance-weighted equivalent level.

Properties:

- drain-only MVG/OLF merges have no infiltration-level tension;
- infiltration-capable merges can have zero tension when the source
  infiltration/drainage conductance ratios are equal;
- a positive value identifies an irreducible one-level representation
  compromise, not a conductance-conservation failure.

Current compression continues to use the drainage-conductance-weighted level.
That choice is **not yet production-admitted for all infiltration-capable
merges**.

The 10,242-HRU population diagnostic now reports:
- the gap on every merge event;
- p50/p90/p95/p99/max over all merges;
- the same distribution for merges involving H1;
- the number of merge events with a positive gap.

No scientific acceptance threshold is defined before the real population
distribution is observed.

Status:

`INFILTRATION_CAPABLE_MERGE_LEVEL_EQUIVALENCE_DIAGNOSTIC_REQUIRED`.


## Activation-breakpoint loss diagnostic — 2026-10-07

The drainage-versus-infiltration centroid-gap diagnostic is necessary but not sufficient to establish hydraulic equivalence of a compressed level.

Even when two infiltration-capable source systems have proportional drainage and infiltration conductances, so that the drainage-weighted and infiltration-weighted equivalent levels coincide, the two physical source levels may still differ.

A one-level SWAP representation then collapses two physical activation breakpoints into one. Between those source levels, the uncompressed system can have a different combination of drainage/infiltration states than any single equivalent SWAP level can reproduce exactly.

Therefore every merge now records two additional quantities.

### Source activation-level span

`max_source_level_separation_m`

Definition:

the maximum absolute separation, over the relevant seasonal or explicit dynamic level timestamps, between the two physical prescribed source levels being merged.

Interpretation:
- zero: no activation-level separation attributable to prescribed level;
- positive: at least two physical activation thresholds are collapsed into one SWAP threshold;
- a zero drainage/infiltration centroid gap does **not** imply this metric is zero.

### Bottom-depth span

`bottom_depth_separation_m`

Definition:

the absolute difference between the two source drainage-bottom depths before merging.

This exposes an additional structural simplification hidden by a conductance-weighted equivalent bottom.

### Population reporting

The 10,242-HRU diagnostic must report, at minimum:

- source activation-level span p50/p90/p95/p99/max over all merge events;
- the same quantiles for H1-involving merges;
- number of merge events with positive source-level span;
- bottom-depth span p50/p90/p95/p99/max;
- drainage-versus-infiltration centroid-gap distributions;
- merge pair frequencies and merge costs.

No production acceptance threshold is defined before these real-population distributions are observed.

Current status:

`MERGE_CONDUCTANCE_CONSERVATION_PROVEN_LEVEL_EQUIVALENCE_NOT_YET_ADMITTED`.

This makes the intended admission logic explicit:

1. exact source lineage preservation;
2. exact drainage/infiltration conductance conservation;
3. quantify source activation-breakpoint loss;
4. quantify drainage-versus-infiltration centroid tension;
5. quantify bottom-depth collapse;
6. assess the real 10,242-HRU distribution and SWAP sensitivity;
7. only then decide whether the five-level representation is scientifically acceptable.


## P/S/T static-bottom authority refinement — 2026-10-07

The NHI/LHM source authority exposes seasonal P/S/T river bottoms:
- P: BODH_P1Z / BODH_P1W;
- S: BODH_S1Z / BODH_S1W;
- T: the supplied LHM INI binds rbot to PEIL_T1Z / PEIL_T1W.

The historical HRU-DRA control instead references downstream steady-state
BODH_P1J / BODH_S1J / BODH_T1J files. Those are not required NHI/LHM source
files and may be absent from the model root.

SWAP method 3 has one static ZBOTDR per drainage level. The 10,242 diagnostic
therefore uses:

- LHM_EQUAL_SEASON_MEAN as reproducible baseline candidate;
- LHM_DEEPEST and LHM_SHALLOWEST as bounded source-based sensitivity cases;
- historical J-bottom as an optional fourth comparison when recovered.

Because the LHM summer/winter regimes each span half a year, the arithmetic
mean is the equal-time least-squares static-bottom candidate. This is a
diagnostic candidate, not production admission.

The diagnostic reports the number of HRUs whose compressed lineage/grouping
changes across these bottom candidates. A sensitive population requires a
subsequent SWAP response sensitivity before bottom reduction can be admitted.

## Legacy high-resistance deactivation refinement — 2026-10-07

Supplied v0.38 deactivates a drainage system when DRARES > 20000 d and disables
the historical pipe system for nature HRUs.

Those rules remain available as historical compatibility semantics.

They are **not** modern physical-source authority: a positive-conductance
physical watercourse must first remain represented through seven-system
aggregation and compression.

The modern diagnostic therefore:
- does not silently deactivate a compressed physical level at 20000 d;
- reports how many levels/HRUs the supplied v0.38 threshold would remove;
- fails closed if any compressed DRARES exceeds SWAP's parser maximum of
  100000 d.

This keeps historical replay and modern corrected production semantics
explicitly separate.


## SWAP method-3 resistance range gate — 2026-10-07

A modern physical drainage component must not be silently altered merely to fit
the SWAP parser range.

SWAP 4.3.1 method 3 accepts:
- DRARES: 1 .. 100000 d;
- INFRES: 0 .. 100000 d.

The modern seven-system aggregation therefore keeps exact equivalent physical
resistance after HRU aggregation and after compression. It no longer clamps
positive physical conductance to 100000 d before diagnostics.

Consequences:
- positive but very weak physical systems remain active during 7->5 compression;
- exact parallel conductance conservation remains meaningful;
- a final compressed DRARES > 100000 d is reported as a SWAP-interface overflow;
- a final compressed INFRES > 100000 d is likewise reported;
- the explicit DRA renderer fails closed on either overflow.

Production requirement:

`ZERO DRARES/INFRES RANGE OVERFLOW`.

If population evidence finds overflow, the resolution must be explicit:
- further physically justified compatible compression; or
- a separately qualified approximation policy.

Silently writing 100000 d is not allowed because it would increase the
represented conductance of a weaker physical system.

This range gate is distinct from the historical v0.38
`drnres > 20000` deactivation heuristic. The latter is reported for legacy
comparison but is not modern physical-source authority.


## Modern SWALLO capability rule — 2026-10-07

Historical HRUlist2SWAP v0.38 disables infiltration when either:
- INFRES > 20000 d; or
- the historical HRU-average river-infiltration diagnostic is < 10.

Those thresholds remain valid historical/replay semantics only.

They are not modern physical-source authority. The modern seven-system route
already carries an explicit hydraulic class per physical/compressed level:

- H1/P/S/T: infiltration-capable open channel;
- MVG/OLF: drain-only open channel;
- PIPE: drain tube / drain-only.

Therefore modern SWALLO is:
- 1 for an infiltration-capable compressed level;
- 3 for a drain-only level.

The exact INFRES remains in the level and is independently subject to the SWAP
method-3 parser range gate (<= 100000 d). A finite qualified LHM infiltration
conductance is never changed to zero solely because an old diagnostic threshold
was crossed.

Historical SWALLO functions and their 49-run regression baseline remain
unchanged and separate.
