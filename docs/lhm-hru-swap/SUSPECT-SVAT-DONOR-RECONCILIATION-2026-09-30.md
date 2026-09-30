# Suspect-SVAT donor reconciliation — 30 September 2026

Status:
**OPERATIONAL REPLACEMENT IN PIET R PROCEDURE CONFIRMED; LEGACY PRE-HRU MARKER ORIGIN SEPARATE**

## Trigger

Project-owner discussion with Leo and Piet states that the replacement cell for the hydrologically suspect SVAT population is selected in Piet's R HRU procedure.

Repository/source review confirms that this is the correct interpretation for the operational donor assignment used by the HRU workflow.

## Suspect population

The current historical qualification population is the union of eight explicit flags:
- ghg_sel;
- gt1_sel;
- gt2_sel;
- gt8_sel;
- kwel_sel;
- wegzijging_sel;
- runoff_sel;
- subinfil_sel.

Historical union:
**20,934 SVATs**.

These cells are diagnostic/suspect targets. They are not automatically numerically overwritten before clustering.

## What Piet's R procedure does

The documented R source `HRU_clustering_LWKM20_31082026.R`:

1. reads the working SVAT table and the original SVAT table;
2. separates valid cells from suspect targets;
3. reconstructs suspect target rows from the original SVAT data, so their own target properties are used rather than copied donor properties;
4. excludes the suspect population from formation of accepted primary HRU clusters;
5. adds the complete suspect population to the post-clustering remainder;
6. assigns those targets to accepted donor HRUs/SVATs through `find_best_matches_ann()`;
7. if still unresolved after two donor rounds, routes them through the `HRUextra` construction;
8. writes the resulting target-to-donor relation in `export_svat_HRU_NRU_10242.csv`.

### Donor round 1

Constraint:
- same LDGB and lu4.

Minimum donor pool:
- 4.

Weighted nearest-neighbour features:
- grondsoort2: 250;
- grondsoort4: 100;
- pawn21 rank: 10;
- Gt: 0.5;
- kwelklasse4: 0.5;
- GHG: 0.01;
- NettoKwel: 0.01.

### Donor round 2

Constraint:
- same LDGB and lu2.

Minimum donor pool:
- 2.

Same feature weights plus:
- lu4 code: 250.

### Final remainder

Still-unmatched targets become `HRUextra`, grouped by:
- LDGB;
- lu4;
- grondsoort4;
- Gt.

The exact subgroup/tie rule for the final donor within HRUextra still deserves source-level regression before historical-exact admission.

## Important distinction: two different donor relations

There is an older/intermediate field `svat_donor` already present in `svat_info_lwkm_new.csv`. For the 20,934 suspect cells this field can differ from the target SVAT before the main HRU clustering stage.

That older relation was previously called a "pre-HRU replacement donor". Its producer has not been bound.

This does **not** mean the operational replacement algorithm is unknown.

The R procedure explicitly rebuilds suspect targets from original data and then assigns them again after accepted HRU clusters have been formed. That later relation is the scientifically relevant operational assignment and is source-bound.

Therefore distinguish:

1. `legacy_pre_hru_donor_svat`
   - observed historical/intermediate marker;
   - producer origin still unresolved;
   - not needed as canonical scientific input.

2. `hru_cluster_donor_svat`
   - produced by Piet's R HRU procedure;
   - operational assignment for suspect/rest targets;
   - source-bound for rounds 1 and 2.

3. `hru_representative_svat`
   - selected later per HRU;
   - separate concept.

## Revised canonical interpretation

The target workflow should be described as:

`source SVAT -> qualification flags -> valid/suspect split -> build HRUs from valid SVATs -> assign suspect/rest targets in Piet donor procedure -> select HRU representative SVAT`.

Do not describe the canonical process as "replace the 20,934 cells first and then cluster".

The legacy pre-HRU donor field can be retained only as regression/provenance evidence unless its producer later becomes scientifically relevant.

## Input needed from project owner

No additional owner input is required to establish that Piet's R procedure performs the operational suspect-cell donor assignment.

Useful later confirmation, if convenient:
- whether the historical `svat_info_lwkm_new.csv` pre-HRU donor field had an intended operational purpose outside the R procedure or was only an intermediate/legacy preparation artifact;
- whether `HRU_clustering_LWKM20_31082026.R` is the exact production version to preserve for historical-exact regression.

Neither point blocks the canonical workflow design described above.
