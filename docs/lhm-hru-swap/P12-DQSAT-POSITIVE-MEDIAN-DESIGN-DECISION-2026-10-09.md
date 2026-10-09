# P12 dqsat selection decision — 2026-10-09

Status: **OWNER-APPROVED PREFERRED METHOD; POPULATION COMPARISON AND SWAP ADMISSION PENDING**

The domain owner approved the **median of strictly positive member-SVAT dqsat values within each HRU** as the preferred method to qualify for modern SWAP drainage spacing. This preference applies to **every HRU**, not just the 14 whose representative SVAT samples zero.

## Policy under qualification

For each HRU, sample the authoritative dqsat raster at every member SVAT's exact cell centre, exclude NODATA and zero values, and compute the median over strictly positive values. Reject negative/non-finite values and HRUs with no positive samples. Set candidate SWAP spacing `L = 4 * median_positive_dqsat`.

Keep three separately named outputs:
- representative-SVAT dqsat (historical qualified source-selection baseline, including its 14 zeros);
- positive-member median (owner-preferred candidate);
- positive-member arithmetic mean (sensitivity comparator).

Do not replace the original source samples or silently change their provenance. This policy is HRU-partition-independent and must be recomputed for any future HRU/SVAT membership change.

## Qualification

Compare all three variants over the full current 10,242-HRU population: counts changed, dqsat and L distributions, relative differences and extreme cases. The current positive-median diagnostic table is available from the 2026-10-08 analysis; preserve it as evidence, not a production shortcut.

Check the sensitivity of SWAP drainage fluxes to L and test representative SWAP runs. The five-level compression grouping can be evaluated separately from L because all active physical systems within one HRU share the same selected spacing, but the final SWAP response cannot be admitted without its spacing qualification.

Production admission remains explicitly **OPEN** until population evidence, physical tests, and interface gates pass. No HRU-specific hardcoding.
