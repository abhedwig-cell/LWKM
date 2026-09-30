# BOFEK lookup reconstruction authority

Goal: replace ambiguous historical bodem370 -> BOFEK lookup with one explicit, provenance-preserving table.

## Primary authority

Use the realized SVAT_INFO_HRU mapping reconstructed from the production workflow.

Observed coverage:
- 365 of 370 bodem370 codes occur in realized SVAT_INFO_HRU;
- absent from realized population: 14, 142, 143, 197, 198.

For every observed bodem370 code, the realized mapping to BOFEK79 was deterministic.

## Known corrections relative to Bodem370_2_bofek2020.csv

Format:
  bodem370: realized_authority / Bodem370_2_bofek2020

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

These differences must not be normalized away. They are consistent with the project-owner recollection that a correction was required to derive the proper BOFEK class from the 370 soil units.

## New lookup schema

Create canonical table with:
- bodem370
- bofek79
- pawn21
- grondsoort4
- grondsoort2
- source
- differs_from_bodem370_2_bofek2020
- reference_bofek2020_value
- status

For 365 observed codes:
  source = REALIZED_SVAT_INFO_HRU
  status = QUALIFIED_REALIZED

For 14,142,143,197,198:
  status = UNOBSERVED_IN_REALIZED_POPULATION
and do not invent a corrected BOFEK79 value solely from absence.

## Rule

Modern SWAP generation derives soil classes from this canonical lookup after selecting Piet's authoritative representative soil/SVAT. It does not recompute BOFEK/soil2 by HRU majority.
