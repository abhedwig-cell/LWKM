# LHM one-to-one MODFLOW / MetaSWAP coupling clarification

Project-owner domain authority:

In LHM the relevant coupling is 1:1: one MetaSWAP SVAT is coupled to one MODFLOW cell. The SVAT active area uopp does not have to equal the full 250 x 250 m = 62,500 m2 MODFLOW cell area.

## Consequence

The MODFLOW cell and the MetaSWAP SVAT have different spatial supports despite the 1:1 identity relation.

MODFLOW_CELL:
- full groundwater accounting cell, 62,500 m2.

METASWAP_SVAT:
- one coupled land-surface unit for that cell;
- active/effective area uopp <= 62,500 m2.

The remainder:
  62,500 - uopp
is not automatically part of the MetaSWAP SVAT water balance. Processes such as precipitation over non-SVAT portions may be handled elsewhere in LHM and can therefore be outside the direct MODFLOW-MetaSWAP coupling visible to this workflow.

## Important invariant correction

Do NOT require:
  MetaSWAP SVAT balance == complete 62,500 m2 MODFLOW-cell surface balance.

Instead distinguish:
1. coupling exchange conservation between the one MODFLOW cell and its one MetaSWAP SVAT;
2. MetaSWAP surface balance over uopp;
3. full MODFLOW-cell accounting, which may include additional domains/processes outside MetaSWAP.

## HRU aggregation

The duplication concern does not apply inside the original LHM 1:1 MODFLOW-SVAT relation.

It becomes relevant only after LWKM groups multiple LHM cells/SVATs into one HRU. At that stage each member corresponds to a distinct MODFLOW cell, but member uopp values can differ.

For MODFLOW-cell intensive quantities such as (h2-h1)/c1, possible HRU weighting choices are therefore:
- equal weight per original MODFLOW cell;
- weight by full MODFLOW cell area (equivalent to equal weight when all are 62,500 m2);
- weight by uopp only if the target quantity is explicitly intended on MetaSWAP-active-area support.

Do not use uopp weighting for a MODFLOW-cell quantity merely because uopp is available.
