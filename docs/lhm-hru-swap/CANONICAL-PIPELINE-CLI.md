# Canonical LWKM pipeline

The replacement workflow now has one orchestration entry point:

python tools/lwkm_pipeline.py status

python tools/lwkm_pipeline.py plan --from-stage A_SVAT

python tools/lwkm_pipeline.py run-ab path/to/SVAT_INFO_HRU.CSV build/canonical

Current executable production slice is A+B: domain/Flevoland/qualification.

The CLI intentionally reports later stages as PARTIAL, SCAFFOLD or NOT_IMPLEMENTED. This prevents architectural scaffolding from being mistaken for scientifically admitted production code.

## Current stage maturity

A SVAT: executable with historical count gates.

B qualification: executable with historical count gate.

C HRU: source-bound components implemented; exact scclust partition adapter and full regression run pending.

D HRU QA: metrics/comparator implemented; waits for candidate output.

E mapping: core mapping implemented; complete field coverage and 2559-sentinel falsification pending.

F SWP: incremental planner and content-addressed artifacts implemented; final legacy/canonical SWP renderer pending.

G runner: restartable state machine implemented; process/executable adapter pending.

H extraction: canonical schema/validator implemented; native SWAP adapter pending.

I acceptance: manifest gate implemented; complete QA policy pending.

J ANIMO: contract boundary understood; serializer not implemented.
