# LWKM waterbalans handoff — 2026-10-14

Status: NUMERICAL COMMON-SUPPORT CANDIDATE; NO FULL BALANCE ADMISSION.

## User-confirmed authority
- 1991–2020 long-term average, combined MetaSWAP + MODFLOW layer 1, with separate MetaSWAP and MODFLOW layer-1 diagnostic subbalances.
- Cumulative WB1 national, WB2 agriculture/nature via `filter_lwkm.asc > 0`, WB3 WB2 + Flevoland FLF correction, WB4 WB3 excluding `verdacht.asc > 0`.
- Do not use `qlat`; unknown lateral boundary fluxes and layer-1 abstractions are missing, not zero.
- MODFLOW original fluxes are m3/cell (62,500 m2); MetaSWAP original fluxes m3/m2 over `UOPP`. Derived annual rasters may already be converted to mm/year.
- Flevoland correction is a layer-1↔layer-2 FLF change. Report FLF-only and FLF plus equal/opposite bookkeeping compensation in surface-water system 1 separately; not a physical rerun.
- End product: Excel-like transparent term-by-term source, sign, units, volume and subtotal table, plus known-term residual explicitly distinguished from numerical model error.

## New common-support calculation
Local script `reconcile_common_support.py` and outputs are packaged as `LWKM_WB_OVERDRACHT_20261014.zip` in the conversation artifacts. It uses source `wbuitvoer(1).zip`, corrected FLF ZIP, `UOPP.ASC`, `filter_lwkm.asc`, `verdacht.asc`; SHA-256 manifest accompanies outputs. No new GitHub Actions requested.

| Variant | Selected cells | Six MetaSWAP terms valid | MODFLOW FLF/RIV/DRN valid | Common valid |
|---|---:|---:|---:|---:|
| WB1 raster domain (national boundary unverified) | 1,351,066 | 645,582 | 1,351,059 | 645,575 |
| WB2 | 427,660 | 427,660 | 427,654 | 427,654 |
| WB3 | 427,660 | 427,660 | 427,654 | 427,654 |
| WB4 | 406,949 | 406,949 | 406,945 | 406,945 |

**Correction of prior analysis:** the previous MetaSWAP WB2 422,080 count required the derived `bdgqmsw` raster to be valid. This is an unnecessary restriction when reconstructing from the six original MetaSWAP terms; the six source terms cover all 427,660 selected WB2 cells. WB2 common support has six MODFLOW-missing cells, WB4 four. Preserve those exclusions as a visible qualification issue, not silent imputation.

The candidate term-volume table uses original six MetaSWAP rasters weighted by UOPP and MODFLOW FLF/RIVDRN weighted by 62,500 m2. These are conditional on final raster-unit and sign qualification. Do **not** sum the six-term diagnostic as an external flux or infer a combined residual. RIV/DRN system components and totals must not be double counted.

## Further work
1. Reconcile source producer/batch/Fortran conversions and signs for all physical terms; identify actual executed paths rather than skipped `goto` branches.
2. Qualify WB1 national mask and six/four MODFLOW NODATA differences.
3. Map original MetaSWAP↔MODFLOW layer-1 coupling and storage; keep unknown lateral flux and abstractions unknown.
4. Build independent subbalance tables and one combined known-term balance, with source-level provenance and a residual only where justified.
5. Compare with historical `SVAT_Waterbalans.xlsx` as diagnostic oracle, not direct production source.
6. Commit reproducible code and evidence; run locally before using GitHub Actions.

Repository branch `work/lhm-hru-swap-workflow-v1`; recheck head at next session. Earlier W00–W14 work remains separate.