# Area normalization reconstruction: uopp and 62,500 m2 cell

## Established from batch logic

The LHM groundwater cell reference area is explicitly configured as 62,500 m2.

uopp.asc is an area grid, copied with a max-62500 gridcalc configuration.

MetaSWAP/land-surface source grids are post-processed as:

  source * uopp / 62500

before filtering and later mm/day products.

Therefore uopp is not merely a binary fraction. It carries an effective area in m2 (bounded by the 62,500 m2 parent-cell area), and source*uopp/62500 converts a SVAT/MetaSWAP intensity to an equivalent intensity on the full MODFLOW-cell support.

This explains why geometric/effective SVAT area cannot be blindly reapplied later: some products have already undergone area-support conversion.

## MODFLOW climate grids

The MODFLOW climate aggregation uses:

  mean(yearly budget grids) / 62.5

with MF_SCALE=62.5.

The consolidated source itself flags /62.5 as a unit conversion requiring verification. Since 62.5 = 62,500 / 1000, the likely dimensional interpretation is conversion between a cell-total volumetric quantity and mm over a 62,500 m2 cell, but this remains a hypothesis until the native MODFLOW budget unit/time basis is bound.

## Consequence

Every intermediate raster must carry a support tag. In particular:
- raw MetaSWAP intensity: SVAT_REPRESENTATION support;
- after *uopp/62500: MODFLOW_CELL-equivalent intensity;
- raw MODFLOW budget: likely MODFLOW_CELL extensive quantity;
- after /62.5: likely MODFLOW_CELL depth-equivalent quantity.

Do not combine or area-weight these again without checking which stage a file belongs to.
