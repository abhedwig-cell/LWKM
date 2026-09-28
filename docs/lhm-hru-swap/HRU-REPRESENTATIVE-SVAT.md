# HRU representative SVAT authority

The final HRU representative SVAT is distinct from the donor used to assign an individual target.

## Historical sequence

1. Build HRU summaries from donor-side attributes.
2. Determine modal categorical representation.
3. For lu2, lu4, grondsoort2, grondsoort4 and pawn21 the script uses a packed numeric combination code and its mode.
4. bodem370, Gt and kwelklasse4 are modal separately.
5. Search actual HRU rows whose donor attributes match the most specific modal code.
6. If no candidate exists, fall back through progressively less-specific packed codes, ultimately to lu2.
7. Within the surviving candidate rows, choose a real SVAT using representative_points(method="medoid") on GHG and NettoKwel.
8. The medoid is the row with minimum mean Euclidean distance to all other candidate rows.

The documentation confirms the hierarchy but does not expose enough of the raw R expressions to bind every packed-code multiplier and tie rule. Do not claim HISTORICAL_EXACT for the fallback encoding until raw R is available.

## Scaling distinction

robust_scalar elsewhere in the R workflow is (x - median) / IQR and returns zero when IQR is zero/NA.

The final representative_points medoid itself is documented as a distance-matrix medoid on GHG/NettoKwel. The canonical helper therefore must not silently substitute MAD scaling.

## Sentinel issue

Negative values such as -999 in downstream representative fields cannot be produced by a successful real-row medoid. They indicate either a later export/schema convention, a failed/unavailable representative lookup, or postprocessing. Until observed historical outputs and raw R code resolve this, the compatibility builder must reject negative representative sentinels rather than interpreting them as physical soil/rooting values.
