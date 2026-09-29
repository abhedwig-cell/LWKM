# SWP generation authority model

## Authority order

1. Datamodel is semantic authority.
2. A named profile defines explicit defaults, supported options and policy choices for one application, e.g. LWKM_2026.
3. Generic context builder resolves datamodel + profile into a complete SWAP render context.
4. Template serializes that context into SWAP syntax.
5. Legacy R/SWAPtools output is regression evidence only.

A realized legacy SWP must never override a contradictory datamodel value merely because it was historically generated that way. A mismatch triggers provenance analysis.

## Genericity

The replacement must preserve Martin's useful design property: templates may contain a much larger set of {{...}} variables and repeated blocks than LWKM currently exercises.

Therefore:
- the renderer is generic;
- LWKM_2026 selects a subset and supplies explicit profile defaults;
- unsupported/missing symbols fail validation;
- unused capabilities remain available without being hard-coded into LWKM logic.

## Resolution precedence

For each render symbol:
1. explicit run/scenario/datamodel value;
2. referenced domain table value;
3. explicit named-profile default;
4. otherwise unresolved -> fail.

There is no silent renderer default.

## Side effects

Rendering SWP has exactly one primary side effect: the requested SWP file.

Other files (CRP, MET, ATM, INI, DRA, BBC, IRG) are separate render/export operations. A template may reference a shared asset without copying it.

## Regression

The 14 generated legacy runs test compatibility of the LWKM_2026 profile. They do not define the generic renderer contract.
