# Owner decision: reconstructed bdgqmsw authority — 2026-10-14

Status: OWNER-APPROVED REPLACEMENT OF HISTORICAL DERIVED RASTER FOR LWKM WATER BALANCE.

The owner confirms that historical `bdgqmsw` was a derived raster with erroneous values in a small number of cells. It is **not** the source of truth for subsequent 1991–2020 water-balance calculations.

Recompute the derived term uniformly for every eligible cell from the six original MetaSWAP components, using the signed producer formula:

```
bdgqmsw_reconstructed =
    (bdgPm + bdgEtact + bdgPsgw + bdgPssw + bdgqrun + bdgdecStot)
    * UOPP / 62500
```

This formula expresses the MetaSWAP source fluxes on a full 250m MODFLOW-cell depth basis. Apply it only after confirming that input rasters are on the expected source unit basis and geometrically aligned. Exclude NODATA from the arithmetic, never silently substitute zero, and retain original sign conventions.

The original `bdgqmsw` raster is **historical comparison evidence only**. It must not be consumed as a numerical balance input, nor used to define the eligible cell mask. The derived term must not be added alongside its six constituents as an independent external flux.

The earlier 62-cell discrepancy audit remains useful provenance for this decision but does not require cell-specific fixes or arbitrary outlier replacement. Use the same general recomputation rule for all eligible cells, including future HRU partitions.

Continue with the WB1–WB4 cumulative masks, FLF correction and separate system-1 bookkeeping compensation. Do not use `qlat`; lateral boundary flow and layer-1 abstraction remain unknown. Combined and subbalance residuals remain unadmitted pending source-unit, sign and boundary reconciliation.

Authority: user confirmation 2026-10-14. This supersedes the earlier status in `docs/handoff/LWKM_WATERBALANS_HANDOFF_2026-10-14.md` that treated reconstructed bdgqmsw as a candidate subject to the 62 historical outliers.
