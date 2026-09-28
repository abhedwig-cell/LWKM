# HANDOFF - canonical LWKM rebuild - 2026-09-28 20:55 CEST

## Current authority
Branch: work/lhm-hru-swap-workflow-v1

Committed code is not automatically admitted production behaviour. Maturity is stage-specific.

## Stage maturity
A SVAT: EXECUTABLE. Domain selection, non-destructive Flevoland correction and count gates implemented.
B qualification: EXECUTABLE. Eight flags, historical count gate and no destructive donor copy.
C HRU: PARTIAL. Eleven-round control-flow, R/scclust compatibility backend, donor matching and assembly structure implemented. Exact HRUextra donor selector and full production regression remain open. Representative selection helper is not yet the complete historical categorical-fallback selector.
D HRU QA: PARTIAL/READY FOR OUTPUT. Label-invariant comparator, route diagnostics and backprojection QA implemented.
E HRU->SWAP: EXECUTABLE_COMPATIBILITY, NOT ADMITTED. Full Runs contract, BBC, DRA and MET core implemented. Negative representative sentinels fail closed. Full historical product regression remains required.
F final SWP: PARTIAL. Incremental planner exists; Datamodel.xlsx/Martin renderer not recovered.
G runner: SCAFFOLD.
H extraction: SCAFFOLD.
I acceptance: SCAFFOLD.
J ANIMO: NOT IMPLEMENTED.

## Regression authorities
- selected SVATs: 427656
- Flevoland changed kwel cells: 4677
- suspected SVATs: 20934
- HRUs: 10242
- NRUs: 25054
- SWAP Runs cases: 10242

## Critical unresolved evidence
1. Exact Deltares Flevoland kwel edit operation.
2. Exact HRUextra donor selector from raw R source.
3. Falsification of 2559 negative representative sentinel rows against realized Runs bodem_id/RDS.
4. Full R/scclust regression on production input.
5. Datamodel.xlsx and Martin SWP renderer, or canonical SWAP-owned replacement.
6. Historical SWAP runner/postprocessing and exact ANIMO exchange writer.

## Defects corrected during consolidation
- Runs area was missing because mapper exposed only area_m2; fixed.
- v0.38 xc/yc are snapped to the nearest real member after centroid calculation, not the raw centroid; fixed.
- compatibility builder now rejects negative representative sentinels.
- CLI maturity synchronized with stage status.

## Next priority
Do not add broad new scaffolding. Highest-value next work is executable regression:
A. materialize source CSVs and run A+B;
B. run historical R and canonical C on identical input with R/scclust;
C. compare HRU partition/routes label-invariantly;
D. run E against historical Runs/BBC/DRA/MET;
E. resolve the 2559 sentinel rows from observed outputs.
