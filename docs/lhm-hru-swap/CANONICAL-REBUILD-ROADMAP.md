# LWKM canonical rebuild roadmap

Date: 28 September 2026
Status: IMPLEMENTATION-READY ROADMAP, HISTORICAL GAPS EXPLICIT

## Target

Replace the current chain of mutable grids, copied CSVs, Fortran preprocessing, R scripts, batch files and manual handoffs by one versioned workflow while preserving current HRU10242/SWAP behaviour as a regression reference.

The rebuild does not require reproducing every historical accident. Every deliberate scientific difference from the historical baseline must instead be explicit and quantified.

## Canonical product graph

LHM_EXPORT -> SVAT_BASE -> SVAT_LBN -> SVAT_FLEVOLAND -> SVAT_QUALIFICATION -> HRU_CLUSTER_INPUT -> HRU_ASSIGNMENT -> HRU_SCHEMA -> SWAP_MAPPING -> SWAP_CASESET -> SWAP_RUN -> HYDRO_EXTRACTION -> QA_ACCEPTANCE -> ANIMO_HYDRO_EXCHANGE

Every arrow owns code/config, manifest, input/output checksums and QA.

## A. Canonical SVAT builder

Implement one builder that reads bound LHM export products and emits immutable SVAT products. Domain selection comes from the versioned land-use lookup. Historical regression target is 427,656 selected SVATs. The old 427,660 filter is a recorded legacy error only.

Flevoland is an explicit correction relation, not an overwritten source field. Current observed regression target is 4,677 corrected kwel cells.

Outputs: svat_base, svat_lbn, flevoland_correction, manifest and QA.

## B. Qualification, not destructive replacement

Implement the eight current qualification rules as data. Persist individual flags, is_valid_for_hru_cluster_building, rule ids and original values.

Historical regression target: 20,934 suspected SVATs.

Do not create a 54-column donor-copied table as canonical state. Preserve an old pre-HRU donor id only as legacy provenance if recovered.

## C. HRU clustering engine

First reproduce the bound R algorithm in a testable module before redesign.

Historical baseline: 11 aggregation/relaxation rounds; valid SVATs build clusters; suspected/rest targets are assigned afterwards; donor matching first within LDGB x lu4, then LDGB x lu2; final HRUextra route; representative SVAT chosen separately; target 10,242 HRUs and 25,054 NRUs.

Persist distinct relations: svat_hru_membership, hru_cluster_donor_svat and hru_representative_svat. Never overload svat_donor.

## D. HRU scientific QA

Backproject HRU state to SVAT level. Mandatory metrics include GHG and NettoKwel MAE/RMSE, area-weighted percentiles, regional LDGB metrics, categorical purity, counts/area through each clustering route and explicit HRUextra/rest cases.

This workunit owns S3->S4 effect attribution.

## E. Declarative HRU->SWAP mapping

Replace HRUlist2SWAP scientific mapping by a declarative mapping engine. For every SWAP target quantity store source product/field, member population, aggregation, representative override, threshold, conversion, fallback and mapping version.

Historical v0.38 is regression profile HRU10242_V038.

Known review items:
- irrigation active code uses 37%, history says 30%;
- SWETR may be stale after representative land-use override;
- dqsat selection precedes representative BFE override;
- drainage member policy differs from comments;
- active QBOT2 is qq, not FLF or FLF+QLAT;
- export_HRUschema_10242_copy.csv contains 2,559 unsafe sentinel rows and must be falsified against realized bodem_id/RDS before use as authority.

## F. Direct SWP generation

Generate SWAP cases directly from the canonical case table and mapping contract. Retain compatibility with standard single-cell SWAP input, eliminate slow generic post-scripting and generate only changed cases when upstream dependencies change.

Content-address generated artifacts. A case manifest records which HRU, mapping, meteo and boundary versions created it.

Do not regenerate all 10,242 cases when only a subset changes.

## G. Run orchestration

Create a runner independent of compute location.

Case states: PLANNED -> STAGED -> RUNNING -> SUCCEEDED/FAILED -> EXTRACTED -> QUALIFIED.

Persist deterministic case id, executable checksum/version, input manifest, status, logs and completeness. Restart only failed or changed cases.

## H. Hydrology extraction

Define a canonical model-neutral extraction table from successful SWAP runs before ANIMO serialization.

Minimum dimensions: run/case, time, soil compartment/interface, state/flux name, value, unit and sign convention.

Native SWAP output is source evidence. QA summaries and ANIMO serialization are derived products.

## I. QA and acceptance

One acceptance manifest binds SVAT authority, qualification version, HRU version, SWAP mapping version, SWAP executable, runset, extraction version and QA result.

No ANIMO handoff from an unqualified runset.

## J. ANIMO adapter

Implement ANIMO serialization as an adapter from accepted canonical hydrology, not as hidden SWAP postprocessing. Legacy binary/unformatted formats such as SWATRE.UNF/SWAP.BUN are compatibility targets where required; canonical hydrology remains format-neutral.

## Regression ladder

1. Domain: 427,656 selected SVATs.
2. Flevoland: 4,677 cells plus bound national/affected-area diagnostics.
3. Qualification: 20,934 suspected SVATs with exact flag overlap.
4. HRU: 10,242 HRUs / 25,054 NRUs plus route and backprojection diagnostics.
5. HRU->SWAP: 10,242 cases and field-level comparison against current run table where historical authority is safe.
6. Selected golden SWAP cases reproduce native output within declared numerical tolerances.
7. Full runset completeness and hydrological QA.
8. ANIMO adapter schema/roundtrip validation.

## Historical gaps that do not block implementation

- exact Deltares operation that edited Flevoland kwel;
- producer of legacy initial 20,934 donor ids;
- provenance of the 2,559 schema-copy sentinel rows;
- compiler flags for historical HRU2SWAP.exe;
- missing historical SWAP runner/postprocessor.

Observed historical products remain regression evidence until a producer is recovered.

## Implementation order

A+B first, then C+D, then E+F in regression mode, then G+H+I, then J.

This allows the old chain to remain operational while the new chain is qualified stage by stage.
