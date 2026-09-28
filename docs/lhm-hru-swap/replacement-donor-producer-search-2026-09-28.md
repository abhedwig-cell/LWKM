# Replacement donor producer search — 2026-09-28

Status: **OPEN, narrowed**

The current data prove that 20,934 hydrologically flagged SVATs receive a pre-HRU replacement donor, but the donor-selection producer is not yet bound.

Search of the previously supplied Fortran source archive found suspicious-cell handling in `LWKM_makeHRU.f90` and `hrulist2SWAP.f90`, but no routine that selects these 20,934 donors. `LHM2SWAP.zip` contains `svat.csv` and `svat_cor.csv`; the latter represents the broader 57,880 changed-SVAT layer and therefore cannot be treated as the pure pre-HRU producer.

The remaining highest-priority source is `HRU-NRU schematisering.7z`. According to the handoff it is stored in Library `/LWKM-reconstruction`, but the current Library folder interface does not expose its raw file entry, so the archive could not yet be inspected in this runtime.

Until producer evidence is found, the observed 20,934 target-to-donor mapping may be used as historical observed output, not as a reconstructed canonical algorithm.

Before admission, bind candidate donor population, matching variables, score/distance, grouping constraints, tie-breaking, no-match handling and relation to the eight qualification flags.
