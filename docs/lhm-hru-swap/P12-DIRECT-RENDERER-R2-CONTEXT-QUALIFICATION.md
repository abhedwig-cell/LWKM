# P12 direct SWP renderer R2 context qualification — 2026-09-30

## Decision

Status:
**QUALIFIED R2 CONTEXT CANDIDATE**

This qualification closes the datamodel-to-render-context layer for the recovered 10,242-run LWKM datamodel. It does not yet admit the complete direct renderer into production because the current production template bytes and the intended 49-run realized SWP regression set remain unavailable through an authorized raw path.

## Evidence set

Recovered raw historical datamodel:
- file: `Datamodel_10242.sqlite`
- SHA-256: `4b697e7f806d0e6f0c345b92bb78c456238c3af5634559a7e2f7edd4171183bb`
- recovered from the raw-readable historical `Datamodel_9830.zip` archive.

Independent realized run-2000 oracle:
- `swap.swp`: `6b47cec011749041bc99e78322ed99a4116b798ec67536969074984f96a49796`
- `2000.bbc`: `fe1aa408e2be00ae261dfe1f9244a682d525707e24aef63da421e6f134bafc1c`
- `2000.dra`: `85dff23754d138b12e3084e5c06c6ad3eb77880c64d7a24f85aa48aae4acd15e`
- `2000.met`: `2598998b5c161aedb9d39c6e3ea8919c78b9a9efbf909506f2a0dfa163a5a8f4`

The loose SWP is internally tied to run 2000 through METFIL, DRFIL and BBCFIL references.

## Reproducible audit result

The recovered SQLite has 10,242 Runs rows.

Required renderer-domain completeness:
- missing discretisatie joins: 0;
- missing eigenschappen joins: 0;
- missing crop-rotation joins: 0;
- missing Output joins: 0;
- missing Gewasweerstand joins: 0;
- missing Scenario joins: 0;
- DZNEW count versus NUMNODNEW mismatches: 0;
- eigenschappen rows with null ELAS: 0.

Observed population:
- scenario_id `direct`: 10,242;
- SWINCO 2: 10,242;
- SWBBCFILE 0: 2,067;
- SWBBCFILE 1: 8,175;
- SWBOTB 7: 2,067;
- SWBOTB 2: 8,175;
- SWETR 0: 7,162;
- SWETR 1: 3,080;
- irrigation_id 0: 9,321;
- irrigation_id 1: 637;
- irrigation_id 2: 284;
- TSTART day offset 365: 10,242;
- TEND day offset 18,992: 10,242.

The audit is implemented in:
- `tools/audit_swp_datamodel.py`;
- `tests/test_audit_swp_datamodel.py`.

## RDS authority closure

The Wortelzone join is complete for all runs when joined through `soil_id + croporg_id`, but its RDS differs from Runs.RDS for 4,350 of 10,242 runs.

This is not treated as unresolved renderer precedence.

Repository authority already establishes that the current production representative root depth comes from Piet's HRU schema. That value is propagated into Runs.RDS. Therefore:
- `Runs.RDS` is production rendering authority;
- `Wortelzone.RDS` is QA-only historical/domain evidence;
- a mismatch is diagnostic and must not block rendering or overwrite Runs.RDS.

Run 2000 is independently discriminating:
- realized SWP RDS = 40 cm;
- Runs.RDS = 40 cm.

This also falsifies the earlier interpretation that 120 cm might be a global hidden renderer default.

## Other context closures

The recovered current datamodel resolves directly or by complete domain join:
- TSTART and TEND;
- NUMNODNEW and DZNEW;
- METFIL;
- SWETR;
- crop rotation;
- SWINCO and GWLI;
- PONDMX and RSRO;
- RSOIL;
- soil profile;
- hydraulic rows including ELAS;
- soil textures;
- RDS;
- SWDRA;
- DRFIL;
- SWBBCFILE, BBCFIL and SWBOTB.

BBC, DRA and MET contents remain separate producer artifacts. The main renderer serializes references to them and does not recreate their scientific calculations.

## Run-2000 context gate

The realized run-2000 oracle is persisted in:
`tests/fixtures/swp/run_2000_semantics.json`.

Regression support:
- `tools/swp_semantic_oracle.py`;
- `tools/compare_swp_semantics.py`;
- `tools/compare_swp_context.py`.

The separation is deliberate:
1. compare resolved datamodel context against realized semantics;
2. then compare rendered SWP against the same oracle.

This prevents template formatting from hiding a scientific mapping error.

## Incremental regeneration closure

The main-SWP fingerprint now covers:
- global configuration;
- simulation/output configuration;
- forcing reference;
- crop rotation;
- initial condition;
- soil profile;
- soil hydraulics;
- soil texture;
- rooting;
- drainage reference;
- bottom-boundary reference;
- run identity.

A change in one of these classes therefore invalidates the affected SWP rather than being silently classified as unchanged.

## Negative result: recovered old template is not production authority

The raw-readable historical archive contains `swap_wwl.swp`. It is useful for recovering the create-SWAP/template mapping, but it cannot be admitted as the current template.

Concrete counterexample:
- active `SWETR = 0` is hard-coded in that template;
- the current 10,242 datamodel contains 3,080 runs with SWETR = 1.

The old template also contains historical hard-coded/commented alternatives around fields such as SWDRA and RSOIL. These are useful provenance evidence but not a safe production contract.

Classification:
**HISTORICAL_MAPPING_ORACLE_ONLY**

## Admission boundary

R2 context qualification is complete enough to proceed to serialization admission.

Still required before `DIRECT_SWP_RENDERER_ADMITTED`:
1. fix an explicit current canonical template contract, preferably from the actual current Template package or a deliberately versioned replacement;
2. render run 2000 and pass the semantic oracle;
3. expand to the intended 49-run regression set;
4. classify every difference as exact-equivalent or an intentional qualified scientific correction;
5. keep the selective-regeneration tests green.

No further scientific majority/representative decisions belong inside the renderer.
