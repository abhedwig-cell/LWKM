# P12 modernization workboard after producer reconstruction

## Production authority established
- Piet HRU schema: representative SVAT, soil/profile, land use, root depth.
- realized SVAT_INFO classification chain for canonical soil lookup.
- uopp for active-surface weighting.
- MODFLOW full-cell support for drainage conductance.
- all-member meteo district majority.
- calibrated irrigation threshold 0.37.

## Producer status

BBC
  reconstructed; prescribed-flux membership/executable provenance remains a reconciliation item.

DRA
  core conductance/depth/level algebra reconstructed;
  full realized numeric gate awaits working local runtime on supplied raw rasters;
  dqsat and nature ordering defects identified.

MET
  district + WET production-qualified on 49 runs / 17,885 rows;
  RAIN/ETref algebra and sparse uopp aggregation implemented;
  same-period realized grid gate remains.

STATIC/RUN
  schema-first model implemented;
  Runs replacement typed record implemented;
  landuse and dqsat authority-order defects identified;
  soil2 authority resolved through lookup;
  RDS defect scoped as overridden in representative mode.

SOIL LOOKUP
  raw SVAT_INFO supplied;
  canonical builder and ten correction guards implemented;
  final 370-row generated artifact blocked only by current local runtime failure.

R TEMPLATE REPLACEMENT
  field authority contract complete;
  next implementation is direct SWP renderer against realized SWP fixtures.

## Remaining scientific/open semantics
- GWLI support/initial-state meaning.
- infil_avg source semantics and SWALLO.
- dqsat representative-soil binding choice, to be resolved with realized L/4 oracle.
- five unobserved bodem370 codes need authoritative classification if future inputs use them.

## Do not reopen without evidence
- 0.37 irrigation threshold.
- all-member DRA population.
- MODFLOW 62,500 m2 conductance support.
- uopp weighting for RAIN/ETref.
- WET dry/wet invariant and historical compatibility policy.
- Piet schema as representative HRU authority.
