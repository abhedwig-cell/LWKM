# MODFLOW FLF producer-stage resolution

The maintained extraction script calls modflowidf2asc with:
- source directory;
- budget item (e.g. bdgflf);
- layer;
- start date;
- end date;
- output ASCII paths.

No explicit 62.5, uopp, area or time-duration scaling argument is supplied by the batch.

Therefore:
- P12's time-varying bdgflf input is upstream of the later climate /62.5 normalization;
- P12 is responsible for its own spatial conversion to SWAP bottom-flux units;
- the native time aggregation performed inside modflowidf2asc remains to be documented from that executable/source or empirical values.

This materially narrows the FLF question: areawb_sum is not a second area normalization applied to an already depth-normalized climate grid. It is the first explicit area denominator visible after native MODFLOW budget extraction.

That still does not prove areawb_sum is the physically correct target area.
