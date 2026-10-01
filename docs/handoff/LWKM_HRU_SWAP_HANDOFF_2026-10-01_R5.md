# LWKM LHM -> SVAT -> HRU -> SWAP handoff R5 — 2026-10-01

## Authority and branch

Repository:
`abhedwig-cell/LWKM`

Work branch:
`work/lhm-hru-swap-workflow-v1`

Head immediately before this R5 write:
`5ac08fe6a6c3b71a017757d6c9120865580fe392`

Repository remains authority.

This R5 handoff supersedes the operational-status parts of R4. R4 and older handoffs remain useful for history and rationale.

Before every write:
1. fetch the actual branch head again;
2. read this R5 handoff;
3. read `docs/handoff/NEXT_CHAT_PROMPT_2026-09-30.txt`;
4. read task-specific authority docs.

## Retained qualified state

Still qualified/closed:
- canonical bodem370 lookup;
- STATIC02 SWETR current population non-discriminating;
- STATIC03 40 soil2 corrections and 6 crop corrections;
- run-2000 direct SWP serialization;
- source collector implementation candidate and Q0-Q4 route;
- semantic recovery of AHN and dqsat source rasters;
- STATIC04 representative-SVAT dqsat source-side authority;
- nature/DRA4 current-population zero expected difference;
- multi-run SWP and DRA regression harnesses;
- Piet R procedure as operational suspect/rest target donor assignment;
- Python LHM raster post-processing compatibility core, with latest pre-R5 CI green at `524a4c857b297ee1383f0caf614ca7d2303fad6d`.

## R5 closure A — raw 49-run realized oracle recovered

User supplied:
`run_files(1).zip`

SHA-256:
`46f1fc6b6f4aa01265db950c8ca78f9c4714a97d11cfa4d8f0c66b4dea7a05e3`

Contents:
- 324 ZIP entries;
- exactly 49 realized HRU directories;
- HRU ids 7866..7945 with gaps;
- every run contains `swap.swp`, run-specific DRA, BBC and MET files.

The former raw 49-run evidence blocker is removed.

## R5 closure B — STATIC04 realized executable behavior

Full 49-run comparison of independently reconstructed source-side hypotheses against realized DRA L/4:

- NON_DISCRIMINATING: 34;
- EXPLAINED_LEGACY: 15;
- EXPLAINED_SCHEMA_FIRST: 0;
- UNEXPLAINED: 0.

Discriminating HRUs:
`7871, 7877, 7909, 7910, 7911, 7920, 7922, 7923, 7927, 7928, 7929, 7930, 7935, 7937, 7942`.

Every discriminating realized run follows legacy majority-BFE dqsat.

Important example:
- HRU 7877 legacy 18;
- representative-SVAT 17;
- realized 18;
- realized L1..L5 all 72 cm.

Historical executable classification:
`STATIC04_49RUN_REALIZED_EXECUTABLE_LEGACY_CONFIRMED`.

Modern authority remains representative-SVAT dqsat.

Therefore the modern candidate must intentionally differ from historical realized DRA spacing on:
- 15 runs;
- five systems each;
- 75 `systems.N.L` paths.

Preregistered:
`config/p12/dra-49run-static04-expected-differences-v1.yml`.

Authority:
`docs/lhm-hru-swap/P12-49RUN-STATIC04-REALIZED-RESULT-2026-10-01.md`.

## R5 closure C — SWALLO 49-run provenance refinement

The earlier run-2000-only label `REALIZED_PRODUCTION_COMPAT` was too broad.

Across 245 realized SWALLO values:
- active supplied v0.38 rule matches 241/245;
- 47/49 runs match completely;
- residuals only in HRUs 7868 and 7929.

The v0.27/run-2000 rule that forces systems 3-5 gives 25/245 mismatches and is falsified as a universal 49-run production rule.

The 49-run archive contains many realized system-3 SWALLO=1 cases.

Revised modes:
- `SUPPLIED_SOURCE_V038`: correct historical baseline for the 49-run archive, with two unresolved source/input provenance residual runs;
- `RUN2000_V027_COMPAT`: scoped only to the separate run-2000/v0.27 provenance state;
- `REALIZED_PRODUCTION_COMPAT` remains only a backward alias for the latter and must not be used as a generic scientific description.

The four residual scalars in HRUs 7868 and 7929 are not qualified intentional differences.

Authority:
`docs/lhm-hru-swap/P12-49RUN-SWALLO-REALIZED-RESULT-2026-10-01.md`.

## Current regression oracle

`config/p12/regression-oracle-v1.yml` is schema version 3 and records:
- raw archive hash and run count;
- STATIC04 source + realized classification;
- 75 expected modern DRA L differences;
- SWALLO v0.38 241/245 match;
- SWALLO residual runs 7868 and 7929;
- universal system-3 force falsification.

## Remaining DRA admission gate

The realized evidence is now available.

Remaining before `DIRECT_DRA_PRODUCER_ADMITTED`:
1. generate the complete modern candidate DRA set from qualified source inputs;
2. run `tools/regress_dra_cases.py` over all 49 runs;
3. accept only preregistered STATIC04 spacing differences and separately qualified provenance differences;
4. investigate HRUs 7868 and 7929 rather than force-fit SWALLO;
5. require zero unexplained DRARES/INFRES/ZBOTDR/LEVEL/SWALLO differences.

Current DRA state:
`REALIZED_ORACLE_RECOVERED_CANDIDATE_GENERATION_FULL_REGRESSION_PENDING`.

## Remaining direct SWP renderer gate

The realized 49 SWP oracles are now available.

The harness exists:
`tools/regress_swp_cases.py`.

A complete execution still needs a raw-readable current 10,242-run renderer database plus the exact versioned legacy mapping template/profile in the active runtime.

Do not substitute guessed spreadsheet parsing when the historical SQLite/template authority can still be recovered from archives/Library.

Once recovered:
1. run all 49;
2. preregister known static intentional differences;
3. require zero unexplained active-SWP differences;
4. assess `DIRECT_SWP_RENDERER_ADMITTED`.

## Python server post-processing line

Implemented:
- `tools/lhm_postprocess.py`;
- `tests/test_lhm_postprocess.py`;
- `docs/server/LHM433_PYTHON_POSTPROCESSING_MIGRATION_2026-09-30.md`.

Latest known green code head before R5 work:
`524a4c857b297ee1383f0caf614ca7d2303fad6d`.

Next production qualification requires a small real LHM-server golden regression against historical Fortran/batch outputs.

## Real NHI/LHM source Q4

Still pending:
- complete authoritative server run tree;
- Q0-Q3 qualification;
- plan;
- collect;
- verify;
- Q4 qualification;
- immutable unpack;
- downstream smoke test.

## Current priority order

1. recover renderer database/template authority and run the 49-run SWP gate;
2. build full modern DRA candidate inputs and run 49-run DRA regression;
3. investigate SWALLO residual HRUs 7868/7929;
4. perform real-server Python post-processing golden regression;
5. perform real-source Q4 bundle qualification;
6. end-to-end 10,242-run production smoke/admission.


## R5 follow-up: raw XLSX recovery and DRA negative diagnostic

The current Datamodel_10242.xlsx and Template.zip are now raw-readable.
The XLSX hash is `5a4e68cb958cb8187639db7750e957c509caf67f81b5b11096c929ca796244d8`.
An explicit cached-value XLSX-to-typed-execution route resolves all 10,242
contexts without missing required joins. SQLite is only an execution format.
The earlier raw-XLSX/Template.zip access blockers are superseded.

The current archive contains wwl.swp, not the exact qualified swap_wwl.swp.
Its different hash and adapter contract prevent silent substitution.
All 20 Library catalog pages and 30 nested alternate archives were searched;
no exact template hash match was recovered. Datamodel_9830 was not used.
The actual XLSX/current-template regression invocation fails at PERIOD=0
adapter expectation. DIRECT_SWP_RENDERER_ADMITTED remains ungranted.

The DRA gate now checks seasonal LEVEL tables and extra assignments.
Native IDF text-provenance footers are supported with strict validation.
An independent 49-run source diagnostic found 226 DRARES, 133 INFRES,
230 ZBOTDR and 230 seasonal-table mismatches across 245 systems.
These differences are unexplained and not intentional. The original
STATIC04 and SWALLO qualified results remain unchanged.
Missing independent length rasters and source/executable-version mismatch
prevent complete DRA producer admission. No production candidate was emitted.

Read `docs/lhm-hru-swap/P12-XLSX-RECOVERY-DRA-DIAGNOSTIC-2026-10-01.md`
and its persisted evidence before the next SWP/DRA action.
No user re-upload is requested.

