# Donor relations and ownership — 28 September 2026

Status: **SEMANTIC OWNERSHIP RECONSTRUCTED**

Three donor/representative concepts occur in the historical chain and must not share one canonical field name.

## 1. Qualification marker / pre-HRU donor

Observed in `svat_info_lwkm_new.csv` for exactly 20,934 hydrologically flagged SVATs.

Downstream role: marks targets as suspected/non-valid for cluster construction. The R source restores original target properties before clustering rather than using copied donor properties numerically.

Producer of the initial donor choice remains open. For modernization, the essential information is the qualification status; a pre-clustering donor value is not required to reproduce the intended cluster-building semantics.

Recommended fields:

- `is_valid_for_hru_cluster_building`;
- `qualification_reason_ids`;
- optional `legacy_pre_hru_donor_svat` retained only for regression/provenance.

## 2. HRU cluster/rest donor

Produced by the HRU clustering source after valid clusters have been formed. Remaining/suspected targets are assigned by progressively broader matching and extra-HRU construction.

This relation appears in `export_svat_HRU_NRU_10242.csv` and is broader than the 20,934 qualification set.

Recommended field: `hru_cluster_donor_svat`.

`LWKM_makeHRU` later reads this relation for an auxiliary discharge diagnostic. Its source comment explicitly describes selected discharge for SVATs used in HRU derivation as `svat_orig = svat_donor`. Thus `LWKM_makeHRU` is a consumer, not the producer, of this relation.

## 3. HRU representative SVAT

Produced in the HRU schema after clustering using categorical matching/fallback plus a GHG/NettoKwel medoid.

Recommended field: `hru_representative_svat`.

This is consumed by HRUlist2SWAP and is not equivalent to either donor relation above.

## Canonical rule

Never expose a generic unqualified `svat_donor` across workflow boundaries. Every relation must state its owner, production stage and purpose.
