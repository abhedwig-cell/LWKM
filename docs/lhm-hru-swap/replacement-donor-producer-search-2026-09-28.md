# Replacement donor producer search — 2026-09-28

Status: **OPEN, narrowed**

The current data prove that 20,934 hydrologically flagged SVATs receive a pre-HRU replacement donor, but the donor-selection producer is not yet bound.

Search of the previously supplied Fortran source archive found suspicious-cell handling in `LWKM_makeHRU.f90` and `hrulist2SWAP.f90`, but no routine that selects these 20,934 donors. `LHM2SWAP.zip` contains `svat.csv` and `svat_cor.csv`; the latter represents the broader 57,880 changed-SVAT layer and therefore cannot be treated as the pure pre-HRU producer.

The remaining highest-priority source is `HRU-NRU schematisering.7z`. According to the handoff it is stored in Library `/LWKM-reconstruction`, but the current Library folder interface does not expose its raw file entry, so the archive could not yet be inspected in this runtime.

Until producer evidence is found, the observed 20,934 target-to-donor mapping may be used as historical observed output, not as a reconstructed canonical algorithm.

Before admission, bind candidate donor population, matching variables, score/distance, grouping constraints, tie-breaking, no-match handling and relation to the eight qualification flags.


## Superseded clarification — 30 September 2026

This note used the phrase "pre-HRU replacement donor" too broadly.

Later source reconciliation plus project-owner discussion with Leo and Piet establish that the operational replacement/assignment of suspect SVATs is performed inside Piet's R HRU procedure after valid clusters have been built.

What remains open is only the producer of the older `svat_donor` field already present in `svat_info_lwkm_new.csv`. That legacy intermediate relation is not required as canonical scientific input because the R procedure reconstructs suspect targets from original SVAT values and performs its own donor assignment.

Authority:
`SUSPECT-SVAT-DONOR-RECONCILIATION-2026-09-30.md`.
