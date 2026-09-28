# GridCalc semantics resolved for suspicious-cell reconstruction

Source-reviewed GridCalc documentation states that chained operations are evaluated strictly left-to-right. There is no arithmetic operator precedence and no expression tree.

Consequences for historical compatibility:

- `kwel + wegzijging / 365.25` evaluates as `(kwel + wegzijging) / 365.25`.
- GT1/GT2 selection commands must be reproduced as sequential numeric raster operations, not rewritten using conventional arithmetic precedence.
- negative intermediate selection values are later clipped by LWKM_makeHRU using MAX(flag,0).

This resolves the earlier operator-precedence blocker.

## Flevoland evidence

control_mkHRU.inp consumes:
- corrected Kwel_1991-2020.asc from LHM_uitvoer/kwel_corr;
- corrected Wegzijging_1991-2020.asc from LHM_uitvoer/kwel_corr;
- kwel_sel.asc and wegzijging_sel.asc also from LHM_uitvoer/kwel_corr;
- original Kwel_1991-2020.asc separately as kwel_org from LHM_uitvoer/filter.

Therefore the final HRU table definitely distinguishes corrected kwel from original kwel, and the two kwel/wegzijging suspicious flags are consumed from the correction directory. This is strong evidence that the correction precedes those final selection products.

Still unresolved: the exact producer commands inside kwel_corr, and whether gt8/kwel_droog_sel was recomputed from corrected kwelwegz or retained from the filter directory. control_mkHRU reads gt8 from LHM_uitvoer/filter/kwel_droog_sel.asc, so do not assume Flevoland correction affects gt8 without direct evidence.
