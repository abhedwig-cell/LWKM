# Flevoland correction policy in qualification

Two policies are deliberately distinguished.

## HISTORICAL_COMPATIBILITY

Evidence from control_mkHRU.inp shows:
- kwel and wegzijging values used by LWKM_makeHRU come from kwel_corr;
- kwel_sel and wegzijging_sel also come from kwel_corr;
- gt8_sel / kwel_droog_sel comes from filter, not kwel_corr.

Therefore historical compatibility preserves this asymmetry. The correction is allowed to alter kwel_sel and wegzijging_sel, but gt8_sel remains the pre-correction filter product unless contrary source evidence is recovered.

## MODERN_CONSISTENT candidate

A future cleaned workflow may decide that every kwel-dependent criterion should see the same corrected kwel state, including GT8. That is a scientific workflow change, not a historical reconstruction, and must be quantified before adoption.

## Sparse correction authority

The target architecture represents the Deltares/Flevoland edit as a sparse SVAT-keyed relation with original and corrected kwel. Historical target: 4,677 changed SVATs.

The unknown historical raster producer is retained as a provenance gap, but no longer needs to be reproduced operationally if the realized correction relation can be reconstructed from before/after SVAT products.
