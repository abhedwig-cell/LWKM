# End-to-end authority status — 28 September 2026

Status: **ACTIVE RECONSTRUCTION**

This register separates an observable/reproducible state transition from provenance of the producer that created it.

| Step | Current authority | Status | Remaining gap |
|---|---|---|---|
| LHM export → S0 | broad SVAT_INFO source plus LHM export contract | PARTIAL | exact technical NL-domain authority and exact current 552705-vs-older-552834 lineage |
| S0 → S1 agriculture+nature | `islwkm=1 <=> lu2 in {1,2}` on bound current HRU10242 source | RECONSTRUCTED | bind modern landuse lookup/version as canonical producer; historical four-cell filter error is not a rule |
| S1 → S2 Flevoland | `kwel_org(mm/j) → kwel(mm/j)`, 4677 SVATs | RECONSTRUCTED TRANSFORMATION | exact Deltares postprocessing script/procedure and delivery provenance |
| S2 → S3 hydrological replacement | 20934 flagged targets and exact observed target→replacement-donor mapping in `svat_info_lwkm_new.csv` | OUTPUT RECONSTRUCTED | donor-selection producer/algorithm |
| S3 → S4 HRU10242 | R source, parameters, processed/original inputs and LDGB mapping bound; observed 10242-HRU products available | SOURCE BOUND, REPRODUCTION OPEN | rerun exact R source and byte/semantic compare outputs |
| HRU10242 → SWAP input | HRUlist2SWAP v0.38 source + exact production control bound | SOURCE/CONTROL BOUND | bind HRU2SWAP.exe binary to source; reconcile copied HRU schema; resolve documented mapping review items |
| SWAP run | run period/control semantics partly bound | PARTIAL | exact executable/runtime package and distributed run manifest |
| SWAP postprocessing | downstream result concept documented | OPEN | exact postprocessing producer, result CSV schema and QA |
| SWAP → ANIMO handoff | architecture target only | OPEN | explicit handoff contract |

## Rules

1. An unknown producer does not invalidate an exactly observed transformation, but it limits provenance status.
2. No open downstream step may silently redefine an upstream state.
3. The current five-stage effect accounting may use observed historical outputs when clearly labelled as observed-output authority.
4. Modernization should replace opaque historical materializations with explicit target/source relations and manifests, without changing historical scientific behaviour until separately qualified.
