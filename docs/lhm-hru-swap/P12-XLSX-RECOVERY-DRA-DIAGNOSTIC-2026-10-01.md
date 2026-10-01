# Current XLSX recovery and independent DRA diagnostic

Base: `3d3c527ece8f2413aa1005685fb46b9567a22bff` on `work/lhm-hru-swap-workflow-v1`.

## Qualified result

`CURRENT_XLSX_RAW_RECOVERED_TYPED_INGESTION_CONTEXT_GATE_CLOSED`.

The current Datamodel_10242.xlsx was recovered as raw bytes from both
`/LWKM/Datamodel_10242.xlsx` and `/LWKM-runtime-recovery/Datamodel_10242.xlsx`.
Both copies have SHA-256
`5a4e68cb958cb8187639db7750e957c509caf67f81b5b11096c929ca796244d8`.
Both contain the same 22 sheets and 10,242 Runs records.

`tools/xlsx_datamodel.py` reads complete worksheets into a temporary SQLite
execution representation for the existing explicit join engine. SQLite is
not a separate scientific authority. Dates become ISO dates, native numbers
remain numeric and blanks become SQL NULL. Empty rows are omitted and
unnamed columns are allowed only when entirely blank. Headers are validated.
All transferred records are checked against their typed SQL roundtrip.
Excel error cells and formulas without cached values fail closed.

337,098 formula cells have saved values. This is ingestion of the supplied
workbook's saved state, not independent recalculation or proof that caches
are current. No scientific values are recomputed or guessed.

The complete current workbook generates 10,242 contexts with zero unresolved
joins/required-field issues using the existing context validator. All 49
realized run IDs also resolve without issues. This closes the raw-datamodel
access blocker and the context completeness gate, not SWP production admission.

Evidence: `docs/evidence/2026-10-01/xlsx-ingestion.json` and
`docs/evidence/2026-10-01/context-10242.json`.

## Template search and failed substitution route

The Library catalog was crawled to completion: 20 pages of up to 200 items.
Exact filename searches, prior-conversation retrieval and repository evidence
were also inspected. No loose `swap_wwl.swp` is exposed by that catalog.
The previously documented hash remains
`d960f7ede8074672f8f8d6c938df0554383f631e75dfdb67ea33bfe15cc5beab`.
Datamodel_9830.zip was not opened or used.

Both current Template.zip copies are now raw-readable and byte-identical:
`f21a15697332184e9931487918243ebf195e8d214ae81c4ca698f9f865f4ef85`.
They contain `Template/wwl.swp`, SHA-256
`ee0c23696fd5565a4b99eb81ce469a1be7c86494cfb20545dfba492820a5858a`.
It is a different template version. Among its differences are PERIOD=1,
additional weather/time/solute symbols and a hydraulic row without ELAS.
It must not be silently substituted for the qualified mapping oracle.

Tools(2).zip was recovered and inspected, including its R source and SWAP
templates. It contains no exact swap_wwl.swp member. The recovered
LWKM_workflow_no_asc.zip contains 2,078 entries but no SWP mapping template.
The supplied source archive and Rscripts archive were also inspected at the
top-level archive inventory. A subsequent recursive scan covered 30 archives
across the supplied source, Rscripts, Tools and the HRU2LSW archive nested in
HRU-NRU schematisering.7z. It found only the different Tools swap.swp and
zero matches to the qualified template hash. See
`docs/evidence/2026-10-01/nested-template-search.json`.
The exact historical template therefore remains unrecovered by the
routes completed here; no claim that the user failed to supply it is made.

`tools/regress_swp_cases.py` now accepts the authoritative XLSX directly.
An actual invocation with current wwl.swp fails before rendering:
`expected exactly one active PERIOD=0 assignment`.
This explicitly falsifies treating that template as compatible with the R2
adapter unchanged. No expected differences were invented to pass it.

Evidence: `docs/evidence/2026-10-01/swp-current-template-attempt.json`.
`DIRECT_SWP_RENDERER_ADMITTED` is not granted.

## DRA gate coverage repaired

The existing DRA comparator omitted seasonal LEVEL tables and ignored extra
global/system assignments. This was a real gap in the requested gate.
The parser/comparator now checks each level date/value, rejects duplicate
dates and detects added assignments. Tests demonstrate changed and missing
LEVEL rows failing independently of scalar equality.

Native IDF sources also contain an iMOD text provenance footer after the
raster. The former reader rejected these files by strict whole-file length.
The reader now accepts only the observed one-record, four-byte-word-length
text footer format, checks its complete length/content and leaves raster
values unchanged. Unknown/truncated footers remain fatal. Original inputs
are retained; no production data files are truncated or rewritten.

## Independent DRA source diagnostic

`tools/diagnose_dra_fields.py` compares the available independent source
inputs against all 49 realized DRA files. It uses all original member cells,
full 62,500 m2 MODFLOW support, native conductance/infiltration rasters and
conductance-weighted depths/levels under supplied v0.38 semantics.
It emits a diagnostic report only, never production DRA files.

Inputs include the current 10,242 membership CSV, full AHN raster,
regionaal.zip, drn.zip and RIV_INFILTRATIE_1991-2020.IDF from
LWKM_workflow_no_asc.zip. The infiltration IDF's embedded provenance names
the corresponding LHM433 FILTER ASC source. That is a provenance clue, not
proof of identity with the exact historical executable inputs.
Source hashes are persisted in the summary.

Results over 245 systems:

| Field | Mismatching systems |
| --- | ---: |
| DRARES | 226 |
| INFRES | 133 |
| ZBOTDR | 230 |
| Seasonal LEVEL table | 230 |
| SWALLO | 3 |

The diagnostic SWALLO residuals are (7870,1), (7922,3), (7929,3).
These are **not** the previously qualified 49-run SWALLO comparison using
historical realized INFRES and its prior input reconstruction. They do not
supersede the existing four residuals in HRUs 7868 and 7929. Inputs and
resistance hypotheses differ; the diagnostic must remain separately scoped.

Example HRU 7866: membership has 42 cells, matching current Runs.nusvat.
Mean sampled AHN is -3.466238 m, consistent with Runs.glk=-3.47 after rounding.
System 1 nevertheless gives candidate DRARES=2240 versus realized 4832,
INFRES=6788 versus 14642, ZBOTDR=-197.00 versus -166.26 cm. This rules out
simple numerical rounding as a sufficient explanation for that case.
It does not identify which source/input/executable provenance caused it.

No discrepancy is admitted as an intentional difference. No drainage
resistance, level, SWALLO or nature policy was force-fitted to the oracle.
The 75 preregistered STATIC04 L differences remain unchanged.

Complete generation still needs independently qualified
`lengte_p_250.asc`, `lengte_s_250.asc`, `lengte_t_250.asc` (or an exact
equivalent), plus resolution of the input/executable-version mismatch.
These length maps control the positive-length versus L=100 fallback for
systems 1-3. Their values must not be inferred from realized L or conductance.
L is deliberately excluded from this diagnostic.

Evidence: `docs/evidence/2026-10-01/dra-source-diagnostic.csv` and
`docs/evidence/2026-10-01/dra-source-diagnostic-summary.json`.
`DIRECT_DRA_PRODUCER_ADMITTED` is not granted.

## Validation and next work

Six new unittest methods pass (including three invalid-workbook subcases).
Nine existing context/SWP/DRA assertion tests pass when invoked directly
with temporary-path fixtures. The optional pytest runner is unavailable in
this runtime; no GitHub Actions run was used.
The actual XLSX-to-SWP harness invocation fails honestly at the incompatible
template adapter gate, as recorded above.

Next: recover the exact mapping template from remaining alternate archive
members/repository history without Datamodel_9830; then execute the full
49-run SWP gate. For DRA, bind the native historical input versions and
investigate the large resistance/depth differences before claiming complete
candidate equivalence. Preserve this negative diagnostic as evidence.
No additional user upload is requested.
