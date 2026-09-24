# SVAT table schema from LWKM_makeHRU v0.20

Status: **SOURCE-BOUND DRAFT**  
Authority inspected: `LWKM_makeHRU.f90`, program version 0.20 (May 2026).

This file documents the **current physical CSV interface** produced by the Fortran source. It is not yet the final canonical schema. The canonical workflow will preserve raw/source values in `SVAT_BASE` and place domain, correction and qualification decisions in `SVAT_QUALIFIED`.

## Source-bound findings

- The program writes **75 columns**.
- `*_uopp` fields are derived normalizations, not independent source variables.
- The eight `*_sel` fields are separate qualification signals and must remain separately traceable.
- `islwkm(0/1)` is the explicit downstream domain flag in this table.
- `isverdacht(1010000)` is a composite diagnostic encoding and is not suitable as the sole canonical qualification field.
- `kwel_org(mm/j)` is preserved as a separate comparison/provenance field; its exact relation to `kwel(mm/j)` remains to be bound before the Flevoland correction is formalized.
- There is a source/header inconsistency: the column named `wegzijgingz(mm/j)` is populated from `plotlist%infil` in the inspected source. This must be resolved rather than silently renamed.

## Data dictionary

| # | Current column | Group | Canonical product | Notes |
|---:|---|---|---|---|
| 1 | `svat` | identity/spatial | SVAT_BASE |  |
| 2 | `opp(m2)` | identity/spatial | SVAT_BASE |  |
| 3 | `xc(m)` | identity/spatial | SVAT_BASE |  |
| 4 | `yc(m)` | identity/spatial | SVAT_BASE |  |
| 5 | `district` | identity/spatial | SVAT_BASE |  |
| 6 | `glg(cm-mv)` | groundwater/state | SVAT_BASE |  |
| 7 | `ghg(cm-mv)` | groundwater/state | SVAT_BASE |  |
| 8 | `glg(scale)` | derived class | SVAT_BASE_DERIVED |  |
| 9 | `ghg(scale)` | derived class | SVAT_BASE_DERIVED |  |
| 10 | `neerslag(mm/j)` | hydrology | SVAT_BASE |  |
| 11 | `neerslag_uopp(mm/j)` | area-normalized derived | SVAT_BASE_DERIVED | Derived in LWKM_makeHRU as source value × 62500 / opp(m2); not an independent hydrological source. |
| 12 | `verdamping(mm/j)` | hydrology | SVAT_BASE |  |
| 13 | `verdamping_uopp(mm/j)` | area-normalized derived | SVAT_BASE_DERIVED | Derived in LWKM_makeHRU as source value × 62500 / opp(m2); not an independent hydrological source. |
| 14 | `runoff(mm/j)` | hydrology | SVAT_BASE |  |
| 15 | `runoff_uopp(mm/j)` | area-normalized derived | SVAT_BASE_DERIVED | Derived in LWKM_makeHRU as source value × 62500 / opp(m2); not an independent hydrological source. |
| 16 | `afvoer(mm/j)` | hydrology | SVAT_BASE |  |
| 17 | `afvoer_sys1(mm/j)` | hydrology | SVAT_BASE |  |
| 18 | `afvoer_sys2(mm/j)` | hydrology | SVAT_BASE |  |
| 19 | `afvoer_sys3(mm/j)` | hydrology | SVAT_BASE |  |
| 20 | `afvoer_sys4(mm/j)` | hydrology | SVAT_BASE |  |
| 21 | `afvoer_sys5(mm/j)` | hydrology | SVAT_BASE |  |
| 22 | `aanvoer(mm/j)` | hydrology | SVAT_BASE |  |
| 23 | `aanvoer_sys1(mm/j)` | hydrology | SVAT_BASE |  |
| 24 | `aanvoer_sys2(mm/j)` | hydrology | SVAT_BASE |  |
| 25 | `aanvoer_sys3(mm/j)` | hydrology | SVAT_BASE |  |
| 26 | `wegzijging(mm/j)` | hydrology | SVAT_BASE |  |
| 27 | `kwelwegzijging(mm/j)` | hydrology | SVAT_BASE |  |
| 28 | `kwel(mm/j)` | hydrology | SVAT_BASE |  |
| 29 | `kwelwegz(scale)` | derived class | SVAT_BASE_DERIVED |  |
| 30 | `qlat(mm/j)` | hydrology | SVAT_BASE |  |
| 31 | `qlat(scale)` | derived class | SVAT_BASE_DERIVED |  |
| 32 | `wegzijgingz(mm/j)` | hydrology | SVAT_BASE | SOURCE-CODE MISMATCH: this header position is written from plotlist%infil. Rename only after semantic authority is confirmed. |
| 33 | `buisdr(mm/j)` | hydrology | SVAT_BASE |  |
| 34 | `af/aanvoer_zomer(mm/j)` | hydrology | SVAT_BASE |  |
| 35 | `af/aanvoer_zomer(scale)` | derived class | SVAT_BASE_DERIVED |  |
| 36 | `beregening(mm/j)` | hydrology | SVAT_BASE |  |
| 37 | `beregening_uopp(mm/j)` | area-normalized derived | SVAT_BASE_DERIVED | Derived in LWKM_makeHRU as source value × 62500 / opp(m2); not an independent hydrological source. |
| 38 | `dqsat(m-mv)` | groundwater/state | SVAT_BASE |  |
| 39 | `gt(1-8)` | groundwater/state | SVAT_BASE |  |
| 40 | `landgebruik22` | classification | SVAT_BASE |  |
| 41 | `lu7` | classification | SVAT_BASE |  |
| 42 | `lu4` | classification | SVAT_BASE |  |
| 43 | `lu2` | classification | SVAT_BASE |  |
| 44 | `bodem370` | classification | SVAT_BASE |  |
| 45 | `bofek79` | classification | SVAT_BASE |  |
| 46 | `pawn21` | classification | SVAT_BASE |  |
| 47 | `grondsoort4` | classification | SVAT_BASE |  |
| 48 | `grondsoort2` | classification | SVAT_BASE |  |
| 49 | `kwelklasse4` | derived class | SVAT_BASE_DERIVED |  |
| 50 | `kwelklasse2` | derived class | SVAT_BASE_DERIVED |  |
| 51 | `qlatklasse4` | derived class | SVAT_BASE_DERIVED |  |
| 52 | `qlatklasse2` | derived class | SVAT_BASE_DERIVED |  |
| 53 | `zomerafvoer4` | hydrology | SVAT_BASE |  |
| 54 | `zomerafvoer2` | hydrology | SVAT_BASE |  |
| 55 | `ghg_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 56 | `gt1_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 57 | `gt2_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 58 | `gt8_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 59 | `kwel_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 60 | `wegzijging_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 61 | `runoff_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 62 | `subinfil_sel` | qualification flag | SVAT_QUALIFIED | Keep as separate rule flag; do not collapse into one suspect flag. |
| 63 | `islwkm(0/1)` | domain flag | SVAT_QUALIFIED | Candidate authority for LWKM domain selection; retain source mask/version. |
| 64 | `isberegen(0/1)` | use/classification flag | SVAT_BASE |  |
| 65 | `isdrain(0/1)` | use/classification flag | SVAT_BASE |  |
| 66 | `isverdacht(1010000)` | composite diagnostic | SVAT_QUALIFIED_DERIVED | Encoded composite; never use as the only provenance for qualification. |
| 67 | `Tact(mm/j)` | hydrology | SVAT_BASE |  |
| 68 | `Eic(mm/j)` | hydrology | SVAT_BASE |  |
| 69 | `Ebs(mm/j)` | hydrology | SVAT_BASE |  |
| 70 | `Epd(mm/j)` | hydrology | SVAT_BASE |  |
| 71 | `Esp(mm/j)` | hydrology | SVAT_BASE |  |
| 72 | `dberging(mm/j)` | hydrology | SVAT_BASE |  |
| 73 | `kwel_org(mm/j)` | comparison/provenance | SVAT_BASE | Meaning relative to kwel(mm/j) must be bound before treating as pre-/post-correction. |
| 74 | `qmetaswap(mm/j)` | model provenance/diagnostic | SVAT_BASE |  |
| 75 | `qmodf(mm/j)` | model provenance/diagnostic | SVAT_BASE |  |

## Canonical restructuring

The physical CSV should not remain the scientific authority indefinitely. The target model is:

### SVAT_BASE
Contains immutable identity, geometry, source hydrology, classifications and explicit provenance. Raw values are never overwritten.

### SVAT_BASE_DERIVED
Contains reproducible derived quantities and classes, for example area-normalized values and class encodings. Every derived field must name its expression/configuration.

### SVAT_QUALIFIED
Contains:
- domain flags;
- correction records;
- individual qualification-rule flags;
- downstream usage-policy flags.

### Separate relation tables
Do **not** add HRU donor/replacement semantics into the base table. Keep at least:
- `SVAT_HRU_MAP` for HRU membership;
- `SVAT_CLUSTER_DONOR` for donor matching used by HRU construction;
- `SVAT_REPLACEMENT` for any hydrological replacement policy.

This prevents an HRU donor assignment from being mistaken for a hydrological correction.

## Required follow-up before admission

1. Bind the production `control_mkHRU.inp` to every source field.
2. Resolve `wegzijgingz(mm/j)` versus `plotlist%infil`.
3. Bind the exact meaning and producer of `kwel_org(mm/j)`.
4. Record period and area basis per hydrological variable.
5. Replace the composite `isverdacht` as an authority with explicit rule flags + versioned qualification configuration.
6. Define explicit correction columns/records for the Flevoland correction instead of overwriting hydrology.
