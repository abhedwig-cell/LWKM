# Spatial-support types for modern LHM -> SWAP generation

Never use an unqualified field named 'area' in new producer code.

## MODFLOW_CELL_AREA_M2

Definition:
  fixed plan-view area of the source MODFLOW cell.

For current LHM 250 m grid:
  62,500 m2.

Use for quantities whose native support is the full MODFLOW cell, including MODFLOW drain conductance conversion:
  R_drain = sum(MODFLOW_CELL_AREA_M2) / sum(C_drain).

Do NOT substitute uopp here.

## ACTIVE_SVAT_AREA_M2

Definition:
  MetaSWAP/SVAT active area read from BasicData/grids/uopp.asc.

May be less than 62,500 m2 despite one-to-one MODFLOW-cell <-> SVAT identity.

Use for land-surface intensive forcing represented by the SVAT, including spatial RAIN and ETref aggregation:
  q_HRU = sum(q_i * ACTIVE_SVAT_AREA_M2_i) / sum(ACTIVE_SVAT_AREA_M2_i).

Historical hrulist2SWAP control explicitly binds:
  area = BasicData/grids/uopp.asc

Therefore historical MET RAIN/ETref weighting is already uopp-weighted.

## MEMBER_COUNT

An equal-member mean is equivalent to full-cell-area weighting only for quantities supported on equal 62,500 m2 MODFLOW cells.

Current relevant examples:
- qq=(h2-h1)/c1: equal mean over selected source cells is a MODFLOW-cell mean.
- meteo district majority: member-count majority equals full-cell-area majority because source MODFLOW cells are equal-sized.

It is NOT equivalent to uopp weighting.

## Producer support table

BBC qq:
  native support = MODFLOW cell;
  aggregation = equal selected-cell mean;
  no uopp weighting.

DRA conductance/resistance:
  native support = MODFLOW cell;
  aggregation = parallel conductance;
  area numerator = N * 62,500 m2;
  no uopp weighting.

DRA representative depths/levels:
  weighting = drain conductance, not area.

MET RAIN/ETref:
  native forcing = 1 km meteo pixel sampled by SVAT location;
  HRU support = active SVAT surface;
  weighting = uopp.

MET district selection:
  source = 250 m district classification;
  historical aggregation = member-count majority over all HRU members;
  not uopp-weighted.

## Validation rule

Every aggregation kernel must declare:
- source_support;
- target_support;
- weight_kind.

Allowed weight_kind values:
  EQUAL_SOURCE_CELL
  ACTIVE_SVAT_AREA
  MODFLOW_CELL_AREA
  CONDUCTANCE
  CATEGORY_MAJORITY
  NONE

Any new kernel using a bare 'area' variable fails review.
