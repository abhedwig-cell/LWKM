# Project-leader effect table: canonical calculation specification

Status: **DRAFT EXECUTABLE SPECIFICATION**

This document translates the seven stages in the project-leader request into measurable, non-overlapping effects.

## Principle

A stage effect is only reported when the comparison holds the correct population and semantics constant. The workflow must not mix:

- a change in selected area;
- a change in a value for the same SVAT;
- an HRU representation effect;
- a SWAP model response.

Those are different causal steps.

## Required table

| Stage | Scientific question | Comparison domain | Primary metrics | Current binding |
|---|---|---|---|---|
| LHM4.3 | What is the upstream hydrologic reference? | agreed LHM export domain | N SVATs, area, weighted hydrologic means/distributions | PARTIAL |
| LHM4.3 lbn | What changes because only LWKM agriculture+nature SVATs are retained? | before versus after domain selection | N/area retained/removed, weighted mean delta by hydrologic variable | `islwkm == 1` strong candidate |
| LHM4.3 cor | What changes because known LHM artefacts are corrected? | exactly the same selected SVAT IDs | N changed, changed area, delta per corrected field, regional totals | Flevoland authority still open |
| LHM4.3 rep | What changes because implausible hydrology is excluded/replaced for a stated purpose? | same selected SVAT IDs plus explicit policy | N flags by rule, usage/exclusion count, replacement delta | qualification rules partly bound; replacement policy open |
| LWKM SVATs | What is the effect of running SWAP 1:1 for a representative SVAT? | explicitly bound representative SVAT set | LHM versus SWAP balance/state metrics | representative relation must be fixed |
| LWKM HRUs | What is the effect of HRU aggregation/representation? | original SVAT area represented by HRU10242 | donor/repr MAE/RMSE, area-weighted balance delta, changed classes | HRU10242 current authority |
| LWKM rep | What is the effect of HRU-level replacement/exception policy? | same HRU IDs | changed HRUs, area, balance delta | open |

## Metrics per hydrologic transition

For every stage that changes hydrologic values:

- number of units evaluated;
- number changed;
- area evaluated;
- area changed;
- area-weighted mean before;
- area-weighted mean after;
- area-weighted mean delta;
- area-weighted MAE;
- area-weighted RMSE;
- P01/P50/P99 before and after;
- maximum absolute delta;
- map/list of changed units.

For selection stages additionally:

- units removed;
- area removed;
- land-use composition before/after;
- regional composition before/after.

## Attribution rules

### LHM4.3 → lbn

This is a **selection effect**. Hydrology of retained SVATs is expected not to change. If it does, the stage contains an undocumented correction and fails attribution.

### lbn → cor

Same SVAT keys before and after. A correction record must contain:

`svat_id, variable, source_value, corrected_value, correction_id, reason, config_version`.

### cor → rep

Diagnosis and action are reported separately:

1. rule-hit population;
2. downstream usage policy;
3. replacement relation, only if replacement is actually performed.

### rep → representative SVAT

Cluster donor `svat_donor` and HRU representative `svat_repr` are separate relations and get separate evidence rows.

### representative SVAT → HRU

Report both categorical purity and hydrologic fidelity. The existing HRU method already produces purity and GHG/NettoKwel diagnostics; these should be incorporated rather than recomputed with subtly different definitions.

### HRU → SWAP

A SWAP result comparison is decomposed into:

`LHM reference → HRU input representation → SWAP response`.

Only the second arrow is a SWAP/model response.

## Evidence package

A candidate run writes:

- `stage_hydrology.csv`
- `domain_effect.csv`
- `correction_diagnostics.csv`
- `qualification_counts.csv`
- `hru_mapping_summary.csv`
- `representation_effect.csv`
- later: `swap_input_effect.csv`
- later: `swap_output_effect.csv`
- `qa_summary.json`
- `report.md`

Every final number in the project-leader table must be reproducible from one of these evidence files.

## Fail-closed cases

Do not publish a stage delta when:

- the compared datasets use different units or periods without an explicit conversion;
- the spatial domains differ unintentionally;
- area basis is not known;
- a correction cannot be distinguished from selection;
- a donor relation is being interpreted as a correction without an explicit replacement policy;
- the production source/control cannot be identified;
- the old and new run are not connected to manifests.

## Immediate open authorities

1. exact Flevoland correction producer and mask;
2. exact production `control_mkHRU.inp`;
3. actual R source for HRU10242;
4. explicit replacement/usage policy for implausible SVAT hydrology;
5. SWAP output QA/balance scripts for the current run.
