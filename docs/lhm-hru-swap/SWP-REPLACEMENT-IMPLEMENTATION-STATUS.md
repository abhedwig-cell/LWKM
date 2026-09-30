# SWP replacement implementation status

## Current qualification

Status:
**R3 ONE-RUN SERIALIZATION QUALIFIED CANDIDATE**

The direct renderer has now passed the full run-2000 serialization gate using:
- recovered Datamodel_10242.sqlite;
- recovered historical swap_wwl.swp;
- explicit SWAPtools serialization adapter;
- explicit LWKM_2026 output profile;
- raw realized run-2000 swap.swp oracle.

This is still not DIRECT_SWP_RENDERER_ADMITTED because the intended 49-run realized regression set is not raw-readable in the current environment.

## Implemented and qualified

1. Generic renderer:
   - scalar substitution;
   - repeated table sections;
   - conditional sections;
   - unknown symbols fatal;
   - atomic writes.

2. Scientific context:
   - TSTART/TEND;
   - METFIL/SWETR;
   - crop rotation;
   - SWINCO/GWLI;
   - PONDMX/RSRO/RSOIL;
   - soil profile;
   - hydraulic rows including explicit ELAS;
   - soil texture;
   - RDS;
   - DRA/BBC switches and references.

3. 10,242-run datamodel completeness:
   - zero missing renderer-domain joins;
   - zero ELAS null rows;
   - Runs.RDS is production authority;
   - Wortelzone.RDS is QA only.

4. Historical SWAPtools boundary:
   - top-level create/run/zip/postprocess orchestration recovered from swap_tools.log;
   - direct renderer replaces input serialization only;
   - SWAP execution, ZIP lifecycle and post-processing are separate operations.

5. Historical template adapter:
   - explicit table headers;
   - parameterized SWETR;
   - parameterized output controls SWWBA, PERIOD, SWAUN, SWODAT;
   - hidden template policy is no longer allowed.

6. Renderer/output profile:
   - explicit non-scientific output policy in config/swp-profiles/LWKM_2026.yml;
   - no silent use of historical template output defaults.

7. Selective regeneration:
   fingerprints cover:
   - global config;
   - simulation/output config;
   - forcing reference;
   - crop rotation;
   - initial condition;
   - soil profile;
   - soil hydraulics;
   - texture;
   - rooting;
   - drainage reference;
   - bottom-boundary reference;
   - run identity.

8. Regression tooling:
   - semantic SWP parser/comparator;
   - datamodel-context gate;
   - template adapter tests;
   - run-2000 semantic fixture.

## Run-2000 serialization closure

Raw oracle:
- swap.swp SHA-256
  6b47cec011749041bc99e78322ed99a4116b798ec67536969074984f96a49796.

Recovered historical mapping template:
- swap_wwl.swp SHA-256
  d960f7ede8074672f8f8d6c938df0554383f631e75dfdb67ea33bfe15cc5beab.

After explicit adaptation and profile application:

- active assignment keys checked: 112;
- assignment-key differences: 0;
- crop rotation rows: 56 / 56 equal;
- soil profile rows: 9 / 9 equal;
- soil hydraulic rows: 4 / 4 equal;
- soil texture rows: 4 / 4 equal.

Classification:
**RUN_2000_DIRECT_SERIALIZATION_GATE_CLOSED**.

The earlier reduced semantic gate is therefore superseded by a stronger full-active-assignment comparison for run 2000.

## What was learned about create_SWAP

The recovered historical template omits explicit table-header rows in four dynamic sections. The realized SWP contains them. SWAPtools therefore performs serialization work beyond literal Mustache substitution.

The historical template also hard-coded:
- SWETR = 0;
- SWWBA = 0;
- PERIOD = 0;
- SWAUN = 2;
- SWODAT = 1.

The raw realized run-2000 SWP instead has:
- SWETR = 0 for this run;
- SWWBA = 1;
- PERIOD = 1;
- SWAUN = 0;
- SWODAT = 0;
- a different detailed INLIST_CSV.

These differences are now explicit context/profile values rather than hidden R behavior.

## Blockers removed

No longer blockers:
- RDS authority;
- crop-rotation join;
- ELAS source;
- simulation-date source;
- METFIL source;
- run-2000 template serialization behavior;
- table-header injection behavior;
- SWETR hidden template default;
- output-switch hidden template defaults.

STATIC02 SWETR current-population effect is already closed at 0 / 10,242 mismatches.

STATIC03 canonical soil2/crop authority correction is already qualified:
- 40 soil2 corrections;
- 6 resulting crop_id corrections.

## Remaining admission blockers

### B1 49-run realized SWP regression

This is now the primary direct-renderer blocker.

Need raw access to run_files.zip or equivalent realized cases to:
- test non-zero SWETR runs;
- test multiple crop/soil/profile combinations;
- confirm output-profile constancy or identify run classes;
- classify the six intentional crop corrections and other expected differences;
- demonstrate no unexplained serialization differences.

### B2 current Template.zip confirmation

Current Template.zip raw bytes remain blocked.

This is now confirmatory rather than the only route to admission, because an explicit canonical replacement contract exists:
- recovered historical mapping template;
- deterministic adapter;
- explicit profile.

If the 49-run regression validates this canonicalized template path, current Template.zip is no longer a hard production dependency.

### B3 upstream DRA authority corrections

Still outside the renderer:
- representative-SVAT dqsat authority remains blocked by raw dqsat raster/oracle access;
- DRA system-4 nature discrimination remains blocked by 49-run DRA access.

The renderer must consume qualified upstream values and never re-decide them.

## Admission rule

DIRECT_SWP_RENDERER_ADMITTED requires:
1. 49-run regression with no unexplained differences;
2. explicit expected-difference records for qualified scientific corrections;
3. selective-regeneration tests green;
4. canonical template/profile version fixed in repository.

Run-2000 no longer blocks admission.

The remaining renderer blocker is multi-run evidence, not unresolved serialization architecture.
