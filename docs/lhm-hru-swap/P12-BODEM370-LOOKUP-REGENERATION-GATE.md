# Raw lookup regeneration gate

Status:
**CLOSED — QUALIFIED CANONICAL LOOKUP PERSISTED**

## Original blocker

The current Project file `SVAT_INFO(1).CSV` is located but its backing bytes are not authorized for raw materialization in this environment. Earlier work had therefore stopped before writing the full 370-row lookup.

Snippets were explicitly not considered sufficient.

## Independent raw recovery

A separate raw-readable historical archive, `Datamodel_9830.zip`, contains `SVAT_Waterbalans.xlsx`.

Source hashes:
- `Datamodel_9830.zip`: SHA-256 `7eed8c4e609c490efb8eb7cff998e537cf3530eb742709d44a05f2c36271b2f7`;
- extracted `SVAT_Waterbalans.xlsx`: SHA-256 `3f875c7aa4badd3125be733c85fc8ecd3f703b10e61bc2af11caa59d040f80ea`;
- extracted historical `Datamodel_10242.xlsx`: SHA-256 `5a4e68cb958cb8187639db7750e957c509caf67f81b5b11096c929ca796244d8`.

The workbook sheet `SVAT_INFO` contains 552,705 source rows. Filtering the explicit `islwkm(0/1)=1` field yields exactly **427,656 LWKM SVAT rows**, the same population size already documented from the later realized workflow.

The raw workbook was reduced directly, not by snippets.

## Regeneration result

For the 427,656 LWKM rows:

1. exactly one `(bofek79,pawn21,grondsoort4,grondsoort2)` tuple occurs per observed `bodem370`;
2. observed code count = **365**;
3. unobserved codes are exactly:
   `{14, 142, 143, 197, 198}`;
4. no observed bodem370 has a non-deterministic classification tuple;
5. comparison with the historical `bodem370_2_bofek2020` sheet yields exactly the ten previously persisted corrections:
   - 78: 40 / 39
   - 79: 39 / 40
   - 81: 39 / 44
   - 82: 44 / 39
   - 94: 31 / 28
   - 95: 28 / 31
   - 147: 46 / 41
   - 148: 41 / 46
   - 170: 44 / 39
   - 171: 39 / 44

This independently reproduces every invariant that had previously been recovered from the current realized SVAT_INFO route.

## Canonical product

Persisted:
`config/p12/bodem370_classification_lookup.csv`

Schema:
- bodem370
- bofek79
- pawn21
- grondsoort4
- grondsoort2
- source
- reference_bofek
- differs_from_reference
- status

For 365 observed codes:
- `source = REALIZED_SVAT_INFO`
- `status = QUALIFIED_REALIZED`

For the five unobserved codes:
- classification fields remain blank;
- historical reference BOFEK is retained only as reference evidence;
- `status = UNOBSERVED_IN_REALIZED_POPULATION`.

No value was invented for an unobserved code.

## Regression enforcement

`tools/build_bodem370_lookup.py` validates:
- 370 total rows;
- exactly 365 qualified realized rows;
- exact five-code unobserved set;
- all ten known corrected BOFEK values and their historical reference values.

`tests/test_bodem370_lookup.py` now validates the persisted canonical file in CI.

## Admission consequence

The canonical lookup is admitted for the current 10,242-HRU production population.

Modern production must:
- resolve representative bodem370 first;
- use this canonical table for BOFEK79, PAWN21, grondsoort4 and grondsoort2;
- fail clearly if a future production population uses one of the five currently unobserved codes unless that code has first received explicit authority.

The still-blocked current `SVAT_INFO(1).CSV` is now confirmatory evidence, not a blocker to the canonical lookup.
