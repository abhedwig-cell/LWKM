# Intended role of the pre-HRU replacement donor relation — 28 September 2026

Status: **ROLE RECONSTRUCTED; INITIAL DONOR-SELECTION PRODUCER STILL OPEN**

The R source and its technical documentation clarify why `svat_info_lwkm_new.csv` appears to copy donor properties and then restore original target properties.

## Role in HRU derivation

The 20,934 rows with `svat_donor != svat` define the **suspected/non-valid target population**.

The clustering source:

1. separates valid SVATs (`svat_donor == svat`) from suspected targets;
2. rebuilds suspected targets from original `SVAT_INFO.csv`, retaining their own hydrological/property values;
3. constructs accepted HRU clusters from the valid population through the eleven aggregation/relaxation rounds;
4. only afterwards assigns remaining/suspected targets to suitable donor SVAT/HRU structures;
5. uses progressively broader matching: first LDGB × lu4, then LDGB × lu2, followed by extra-HRU construction for remaining cases.

Therefore the donor-substituted materialization is not intended as the direct numerical clustering state. Its essential role is to identify SVATs that must not participate as valid cluster-building observations and to provide lineage into the replacement/matching workflow.

## Revised interpretation

The clean conceptual semantics are closer to:

`S2 target hydrology → qualify valid/suspected → build HRUs from valid SVATs → assign suspected/rest targets to donor HRUs → choose HRU representative SVATs`.

This is preferable to describing the process as “replace hydrology, then cluster”.

## Canonical recommendation

The modern workflow should therefore not need a full 54-column donor-copied `svat_info_lwkm_new.csv` as an intermediate scientific state.

Persist instead:

- original selected SVAT state;
- qualification flags;
- `is_valid_for_hru_cluster_building`;
- reason/rule ids;
- target→assigned HRU/donor relation produced after valid clusters exist;
- final HRU representative SVAT separately.

This preserves the historical intent while avoiding the confusing copy-then-restore operation.

The exact producer that generated the original 20,934 target→donor relation remains open, but its downstream role is no longer ambiguous.
