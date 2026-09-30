# P12 49-run integrated regression oracle

Purpose: use the supplied 49 realized run directories as one shared executable oracle for BBC, DRA, MET and static Runs/SWP behavior.

## Principle

Do not merely compare outputs that both hypotheses predict identically.

For each observable classify the HRU as:
- NON_DISCRIMINATING: legacy supplied-source and schema-first candidate predict same output;
- DISCRIMINATING: predictions differ;
- SOURCE_MISSING: one required raw source unavailable;
- EXPLAINED_LEGACY;
- EXPLAINED_SCHEMA_FIRST;
- UNEXPLAINED.

Only discriminating cases can establish whether a supplied-source defect was present in the executable that generated the realized runs.

## Observables

### Representative/static
- final bodem/profile id;
- soil2 id;
- land-use id;
- root depth;
- SWETR;
- crop_id/croporg_id.

Hypotheses:
A supplied-source ordering;
B schema-first Piet authority + canonical soil lookup.

### DQSAT / drainage spacing
Observable:
  DRA L1..L5.
For systems with positive source length:
  inferred dqsat = L/4.
Compare:
A dqsat selected under legacy majority BFE;
B dqsat bound to representative soil/SVAT semantics.
Systems with fallback L=100 are non-discriminating for dqsat.

### Nature drainage
Observable:
  system-4 DRA state.
Compare legacy is_nature vs representative-landuse is_nature.
Exclude cases where raw DRARES4 >20000 independently forces shutdown.

### Drainage aggregation
Observables:
  DRARES1..5, INFRES1..5, ZBOTDR1..5, LEVEL1..5.
Formula gate independent of schema-ordering gate.

### MET district / WET
Already qualified:
- 49/49 district majority;
- 17,885/17,885 WET rows explained.
Do not rerun unless source changes.

### BBC
Observable:
  QBOT2 time series and boundary selection.
Keep membership/executable provenance separate from static authority.

### GWLI
Compare realized Runs/SWP GWLI with exact supplied-source formula.
No schema-first replacement is admitted yet; this is historical characterization only.

### SWALLO
Compare realized DRA SWALLO against supplied-source infil_avg/INFRES rule.
No modernization until source infil semantics are bound.

## Output artifact

Produce one CSV:
  hru,observable,legacy_prediction,schema_prediction,realized_value,
  discriminating,classification,max_abs_error,notes

and one summary:
  counts per observable/classification.

## Admission rule

A modern producer may intentionally differ from realized historical output only when:
1. the difference traces to a documented defect/authority correction;
2. the corrected semantics are explicit;
3. unchanged observables remain regression-identical;
4. the difference is recorded, never silently normalized.
