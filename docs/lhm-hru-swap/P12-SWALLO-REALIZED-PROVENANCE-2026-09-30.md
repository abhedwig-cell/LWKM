# P12 SWALLO realized-provenance result — 30 September 2026

Status:
**SOURCE/REALIZED SEMANTIC MISMATCH CONFIRMED; RUN-2000 DISCRIMINATES SYSTEM 3**

## Question

The supplied HRUlist2SWAP v0.38 source renders:

`SWALLO = 3` when:
- `system > 3`, or
- `INFRES > 20000`, or
- `infil_avg < 10`.

Otherwise it renders `SWALLO = 1`.

The source history comment for v0.27 instead says:
`SWALLO=3 voor sys>2`.

The realized run-2000 DRA provides an independent discriminator.

## River-infiltration input binding

HRUlist2SWAP reads:
`riv_infil`
into the per-SVAT variable `infil`, then computes:
`infil_avg = equal-member mean(infil_i)`.

LWKM_makeHRU shows that the same upstream raster is written to `SVAT_INFO_HRU.CSV` in the position labelled:
`wegzijgingz(mm/j)`.

That CSV header is therefore historically misleading for this field. The value is the separate river-infiltration diagnostic, not a soil-hydraulic or representative-soil quantity.

Using:
- `export_svat_HRU_NRU_10242.csv` for exact HRU membership;
- `SVAT_INFO_HRU.CSV` field `wegzijgingz(mm/j)`;

the equal-member river-infiltration indicator is reproducible for all 10,242 HRUs.

Full population:
- HRUs: 10,242;
- `infil_avg < 10`: 6,324;
- `infil_avg >= 10`: 3,918;
- exact equality at 10: 0.

Run 2000:
- reconstructed `infil_avg = 11.8204166667`.

## Realized run-2000 discriminator

Realized `2000.dra` contains:

| system | INFRES | SWALLO |
| ---: | ---: | ---: |
| 1 | 100000 | 3 |
| 2 | 2498 | 1 |
| 3 | 725 | 3 |
| 4 | 100000 | 3 |
| 5 | 100000 | 3 |

For system 3:
- `system = 3`;
- `INFRES3 = 725 < 20000`;
- `infil_avg = 11.82 >= 10`;
- realized `SWALLO3 = 3`.

Therefore the active supplied-source rule `system > 3` predicts `SWALLO3 = 1` and is falsified for the realized run-2000 executable.

The history rule `system > 2` predicts `SWALLO3 = 3` and matches the realized oracle.

This is independent of DRARES, dqsat, nature and representative-SVAT authority.

## Classification

Confirmed:

**SWALLO_SUPPLIED_SOURCE_V038_VS_REALIZED_EXECUTABLE_MISMATCH**

For run 2000 the realized executable behaves consistently with:

`system > 2 OR INFRES > 20000 OR river_infiltration_indicator < 10`.

The current supplied source behaves as:

`system > 3 OR INFRES > 20000 OR river_infiltration_indicator < 10`.

Do not silently normalize one into the other.

## Production implication

The direct DRA renderer needs explicit provenance semantics.

Recommended compatibility split:
- `SUPPLIED_SOURCE_V038`: force SWALLO=3 for systems 4-5 only;
- `REALIZED_PRODUCTION_COMPAT`: force SWALLO=3 for systems 3-5.

The threshold-10 river-infiltration rule and `INFRES > 20000` rule remain common.

Until the 49-run realized archive is accessible, run 2000 establishes the mismatch but not the prevalence of additional system-1/2/3 cases in that oracle.

Direct DRA admission still requires:
- 49-run realized regression;
- explicit expected-difference/provenance policy;
- zero unexplained differences.

