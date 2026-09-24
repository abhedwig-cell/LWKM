# FIVESTEP-01 — Build verified five-stage hydrological chain

Status: **ACTIVE WORK UNIT**  
Date: 24 September 2026

## Objective

Turn the documented five-stage comparison into a real, reproducible and verifiable data chain that produces inspectable hydrological results.

The immediate priority is to establish a trustworthy SVAT base and then construct the five stages from that single authority.

## Target stages

1. **SVAT_NL_BASE**
   - Netherlands modelling domain after purely technical/spatial trimming;
   - original LHM hydrology;
   - no agriculture+nature selection;
   - no Flevoland correction;
   - no extreme-value treatment.

2. **SVAT_LBN**
   - same schema and hydrology;
   - agriculture + nature selection applied explicitly.

3. **SVAT_FLEVOLAND_CORR**
   - same SVAT domain as stage 2;
   - accepted Flevoland hydrological correction applied;
   - affected balance components identified and changed consistently.

4. **SVAT_QUALIFIED_REP**
   - same SVAT domain as stage 3;
   - versioned hydrological plausibility/extreme-value policy applied;
   - all donor/replacement actions traceable.

5. **SVAT_HRU10242_BACKPROJECTED**
   - HRU10242 derived from stage 4;
   - HRU representation mapped back to the same SVAT support for direct comparison.

## First work block: establish the correct SVAT base

Before downstream work is admitted, bind:

- exact LHM export package;
- exact national-domain mask;
- exact agriculture+nature selection mask/rule;
- SVAT key and area;
- period;
- units;
- sign conventions;
- all balance variables required for later comparison;
- checksum and provenance of every source file.

The output of this block is a candidate `SVAT_NL_BASE` plus a manifest and QA report.

## Admission criteria for SVAT_NL_BASE

The base is admitted only if:

- each SVAT key is unique;
- spatial domain is explicit;
- removed foreign/open-water cells can be counted and explained;
- area totals are reproducible;
- no downstream corrections are already embedded;
- Flevoland-corrected values are not mixed silently into the raw state;
- extreme-value replacements are not embedded silently;
- every hydrological column has known unit, sign and period;
- basic water-balance consistency diagnostics are available;
- file checksum and producing source are bound.

## Build order

### A. RECONCILE
Locate current source files, controls, scripts and candidate CSVs.

### B. BIND SOURCE AUTHORITY
Identify which files are raw LHM-derived authority and which are processed copies.

### C. BUILD SVAT_NL_BASE
Produce one canonical same-schema table.

### D. QA SVAT_NL_BASE
Run domain, schema, units, uniqueness, area and hydrological plausibility checks.

### E. BUILD S1 → S4
Apply one transformation at a time and persist each stage separately.

### F. EFFECT ACCOUNTING
For each transition produce:
- national delta;
- regional delta;
- area affected;
- MAE/RMSE;
- percentiles/extremes;
- spatial diagnostics.

### G. ADMIT OR REJECT
A stage only becomes canonical when provenance and QA both pass.

## Key non-negotiable rule

Every downstream stage must consume the exact accepted output of the previous stage. No step may silently substitute another copy of an assumed equivalent SVAT file.

## Immediate evidence tasks

1. bind the exact source for the current SVAT table;
2. verify the current `SVAT_INFO_HRU.CSV` state against raw/corrected/qualified hypotheses;
3. bind the technical Netherlands-domain trimming;
4. bind the agriculture+nature selection;
5. reconstruct the Flevoland correction authority and affected flux terms;
6. reconstruct the extreme-value treatment;
7. verify that HRU10242 was derived from the same qualified SVAT state;
8. only then run the five-stage comparison numerically.

## Deliverables

- `SVAT_NL_BASE.csv`
- `SVAT_LBN.csv`
- `SVAT_FLEVOLAND_CORR.csv`
- `SVAT_QUALIFIED_REP.csv`
- `SVAT_HRU10242_BACKPROJECTED.csv`
- manifest per stage
- QA report per stage
- transition effect tables
- national and regional comparison figures
- exception register
