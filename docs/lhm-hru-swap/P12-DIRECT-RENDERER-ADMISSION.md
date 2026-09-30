# P12 direct renderer admission plan

The R/template layer is no longer allowed to decide scientific values.

## Phase R1 — fixture extraction
From supplied realized run directories capture:
- swap.swp
- referenced .bbc/.dra/.met
- any crop/soil/template fragments required by swap.swp
as immutable regression fixtures.

## Phase R2 — typed substitution
Parse the historical template once into named sections.
Map every {{}} token to:
- P12RunRecord field;
- producer file reference;
- explicit config value;
- external static content reference.

Unknown tokens are fatal. No "generate everything" side effects.

## Phase R3 — selective generation
Dependency hashes:
- representation hash;
- BBC hash;
- DRA hash;
- MET hash;
- renderer/template hash.

Regenerate only outputs whose dependency hash changed.

Examples:
- changed precipitation day -> MET dependency only;
- corrected DRA source -> DRA plus SWP only if SWP embeds rather than references DRA;
- changed representative soil -> soil/profile/crop/SWP and dqsat-dependent DRA, not MET/BBC unless their inputs changed.

## Phase R4 — 49-run regression
For unchanged historical semantics require exact or whitespace-normalized identity.
For intentional defect corrections require explicit expected-difference records.

## Phase R5 — remove R from critical path
Keep historical R procedure only as a comparison fixture/tool, not production dependency.

Admission:
DIRECT_SWP_RENDERER_ADMITTED only after 49-run regression has no unexplained differences.
