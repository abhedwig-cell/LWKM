# S3 → HRU10242 state semantics — 28 September 2026

Status: **SOURCE-BOUND MIXED-STATE TRANSITION**

A critical distinction is required between the materialized pre-HRU replacement table and the actual state used inside the HRU clustering source.

## Materialized pre-HRU state

`svat_info_lwkm_new.csv` contains 427,656 selected SVATs. For exactly 20,934 flagged targets, 54 donor-property fields are copied from `replacement_donor_svat`, while target identity, target coordinates and target area remain.

This is the observed historical S3 replacement artifact.

## What the R clustering source does

`HRU_clustering_LWKM20_31082026.R` reads that processed file as its primary dataset, but identifies rows where `svat_donor != svat`, removes/replaces those rows, and rebuilds them from the original `SVAT_INFO.csv` restricted to `islwkm == 1`.

Therefore the HRU clustering calculation does **not** simply cluster the fully donor-substituted S3 table as materialized.

For the 20,934 replacement targets, original target hydrological/property values are reintroduced for the clustering workflow. The donor relation remains available as lineage/matching information and later donor/rest-group logic creates an additional, broader HRU-cluster donor relation.

## Consequence for five-stage effect accounting

The conceptual chain

`S2 → donor-replaced S3 → HRU(S3)`

is not an exact description of the historical implementation.

Historical HRU10242 instead contains a mixed-state transition:

`S2/selected target state + replacement lineage → HRU clustering/rest-group logic`.

The 20,934-row donor-substituted materialization and the 57,880-row HRU cluster-donor relation are different mechanisms and must remain separate.

## Canonical modernization decision required

For a scientifically transparent new chain, choose explicitly between:

1. **replacement-affects-clustering:** S3 effective donor values are the actual clustering input; or
2. **replacement-does-not-affect-clustering:** original target values drive clustering and replacement is only a downstream/use policy.

Do not preserve the historical mixed behaviour accidentally. If historical equivalence is required, encode it explicitly as a versioned legacy policy and quantify the difference to the cleaner alternatives.
