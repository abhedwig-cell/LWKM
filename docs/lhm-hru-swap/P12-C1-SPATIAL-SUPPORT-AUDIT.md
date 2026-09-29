# C1 spatial-support refinement

Domain authority supplied by project owner:

c1 originates from a MODFLOW input describing vertical resistance between the phreatic layer and the underlying aquifer. Unit: days.

Consequences:
- head_l1 and head_l2 are MODFLOW groundwater heads;
- q = (head_l2 - head_l1) / c1 is a MODFLOW-scale vertical Darcy flux intensity [m/day];
- q is not intrinsically a MetaSWAP/SVAT flux.

## Replication risk

hrulist2SWAP samples MODFLOW-grid quantities through each selected SVAT's row/column and then averages over SVAT members.

If multiple selected SVATs refer to the same MODFLOW cell, identical MODFLOW q values can occur multiple times in the average. This implicitly weights a MODFLOW cell by the number of selected SVATs mapped to it.

That may be intentional only if SVAT multiplicity represents the desired accounting weights. It is not automatically conservative.

## Three formulas to compare

HISTORICAL_SVAT_MEAN:
  mean(q_svat) over issvatwb.

UNIQUE_MF_CELL_MEAN:
  mean(q_cell) over unique MODFLOW cells represented by the HRU.

REPRESENTATION_AREA_MEAN:
  sum(q_svat * A_rep_svat) / sum(A_rep_svat).

Do not select a corrected formula a priori.

## Required audit

For every HRU:
- count selected SVATs;
- count unique MODFLOW row/col cells;
- determine SVAT multiplicity per MODFLOW cell;
- determine whether q differs among SVATs sharing one MODFLOW cell;
- compare all three candidate HRU fluxes;
- reconstruct total represented volume and test conservation against MODFLOW-cell flux * 62,500 m2.

This is now the central test for H-P12-BBC-WEIGHT01.
