# SWP replacement implementation status

## Current qualification

Status:
**R2 CONTEXT QUALIFICATION CANDIDATE**

The renderer architecture and the current 10,242-run datamodel binding are now substantially closed. This is not yet `DIRECT_SWP_RENDERER_ADMITTED`, because the current production template bytes and a 49-run realized SWP regression set are still unavailable through an authorized raw path.

## Implemented and qualified

1. The generic renderer supports scalar and repeated/conditional Mustache-style blocks and fails on unresolved symbols.
2. Rendering is atomic.
3. Auxiliary MET, DRA and BBC scientific production is separate from SWP rendering.
4. The SQLite context builder resolves:
   - simulation dates and numerical controls;
   - MET reference and SWETR;
   - crop rotation;
   - initial groundwater condition;
   - soil profile;
   - hydraulic parameters including explicit ELAS;
   - soil textures;
   - rooting depth;
   - drainage switch/reference;
   - bottom-boundary switch/reference.
5. Runs.RDS is current production authority. Wortelzone.RDS is QA only.
6. The full 10,242-run recovered SQLite has zero missing renderer-domain joins and zero ELAS null rows.
7. Dependency fingerprints cover every identified class that can change the main SWP:
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
8. The dry-run planner can therefore distinguish create/update/skip and report the semantic dependency classes that changed.
9. A semantic SWP parser/comparator exists and ignores irrelevant formatting differences.
10. A separate datamodel-to-oracle context gate exists, so scientific mapping can be tested before template serialization.
11. Current branch CI passes the full unit-test suite.

## Independent run-2000 oracle

Raw realized files are available for:
- `swap.swp`;
- `2000.met`;
- `2000.dra`;
- `2000.bbc`.

The realized SWP and recovered `Datamodel_10242.sqlite` agree on the discriminating main-SWP values checked so far, including:
- dates;
- METFIL and SWETR;
- SWINCO and GWLI;
- PONDMX and RSRO;
- RDS = 40 cm;
- drainage and BBC references;
- SWBOTB;
- NUMNODNEW;
- soil profile;
- hydraulic rows including ELAS = 1e-6;
- soil texture.

The run-2000 result is particularly useful because it falsifies the earlier apparent `RDS=120` constant from the small runs-1-to-14 sample. RDS is run dependent.

## Blockers removed since the earlier status

The following items are no longer semantic blockers:
- RDS authority: Runs.RDS is production authority under the P12 representative-schema contract.
- crop rotation join: complete in the recovered 10,242 datamodel.
- ELAS placement: explicit in `eigenschappen.ELAS`.
- TSTART/TEND placement: explicit in Runs.
- METFIL reference: explicit in Runs.
- BBC time series: not part of main-SWP rendering; it remains a separate producer/file.

## Remaining admission blockers

### B1 Current production template bytes

The historical archive contains `swap_wwl.swp`, but it is not valid as current production authority. Its active SWETR is hard-coded to 0, while 3,080 of the 10,242 current Runs rows require SWETR = 1.

The current Project `Template.zip` has been located, but its backing bytes are not currently authorized for materialization. Until that is resolved, the historical template can be used only as a mapping oracle.

### B2 Realized multi-run SWP regression

One discriminating realized run is available as raw bytes. Admission still requires the intended multi-run regression, ultimately the 49-run oracle, with:
- exact/semantic matches where historical semantics are retained;
- explicit expected differences where known authority-ordering defects are corrected.

### B3 Corrected upstream scientific fields

Renderer correctness does not itself close the upstream P12 corrections for:
- dqsat;
- SWETR/land-use ordering;
- soil2/canonical bodem lookup;
- DRA nature suppression.

Those differences must enter the typed run record as qualified upstream values. The renderer must serialize them without re-deciding them.

## Admission rule

Do not remove Martin's R/SWAPtools path from regression use yet.

`DIRECT_SWP_RENDERER_ADMITTED` requires:
1. production template contract fixed or replaced by an explicitly versioned canonical template;
2. one-run render passes the run-2000 semantic gate from datamodel through serialization;
3. 49-run regression has no unexplained differences;
4. selective-regeneration dependency tests remain green.

The architecture and context are ready for this gate. The remaining blockers are evidence/template admission blockers, not unresolved renderer science.
