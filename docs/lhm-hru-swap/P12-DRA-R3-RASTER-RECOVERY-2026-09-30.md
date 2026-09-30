# P12 DRA R3 raster recovery — 30 September 2026

Status:
**SOURCE RASTER CONTENT RECOVERED; RAW-BYTE IDENTITY STILL UNAVAILABLE**

## Purpose

R3 reported that the two DRA source rasters were present in Project Files but could not be materialized as raw bytes. This note records a non-circular recovery of their numerical contents without treating chat/runtime access behavior as production authority.

Recovered Project files:
- `ahn_f250_m.asc`;
- `grensvlak_NHIWQ_v2_fill.asc`.

Direct raw-file materialization still fails with the Project authorization error. Text line-range materialization does succeed.

## Completeness gate

Both files were recovered in two non-overlapping text line ranges and reassembled in row order.

Both reconstructed grids contain:
- header: 6 lines;
- ncols: 1200;
- nrows: 1300;
- xllcorner: 0;
- yllcorner: 300000;
- cellsize: 250;
- exactly 1300 data rows;
- exactly 1200 numerical values on every data row.

There are therefore exactly 1,560,000 raster cells in each recovered numerical representation.

### AHN / glk

Observed header NODATA value:
`-9999.000`.

Observed numerical range including NODATA:
- minimum: -9999;
- maximum: 320.906;
- NODATA cells: 935,284.

Canonical semantic SHA-256 over the complete row-major IEEE-754 little-endian float64 value array:
`6137121ac628db3330dc48a12e1849cd25dd2169485f24215230317522b8f5f8`.

### DQSAT / grensvlak

Observed header NODATA value:
`-9999`.

Observed numerical range:
- minimum: 0;
- maximum: 20;
- cells equal to -9999: 0.

Canonical semantic SHA-256 over the complete row-major IEEE-754 little-endian float64 value array:
`79fdfc37153aea04a9ec24cef1b3d981f519aaed062f8c07e8922766bb3849cd`.

## Interpretation

The former statement that the source raster contents are unavailable is no longer correct.

The following are now available for scientific reconstruction:
- complete source-SVAT ground-level values from `ahn_f250_m.asc`;
- complete source-SVAT dqsat values from `grensvlak_NHIWQ_v2_fill.asc`;
- exact raster geometry and row/column alignment.

The semantic hashes above are deliberately not presented as hashes of the original raw files. Raw-byte materialization is still blocked, so whitespace/line-ending byte identity with the uploaded originals has not been established.

## Remaining authority dependency

The raster recovery does not by itself identify Piet's representative SVAT per HRU.

Production semantics still require:
1. recover the authoritative `svat_repr` relation from `export_HRUschema_10242.csv` or an exactly equivalent persisted artifact;
2. map that SVAT to its source raster cell using `svat.asc` or another source-bound exact coordinate relation;
3. sample glk and dqsat at that cell;
4. compare representative-SVAT dqsat against historical `Runs.dqsat`;
5. keep realized DRA `L/4` only as a historical oracle, never as the source for representative dqsat.

The current `export_HRUschema_10242_copy.csv` history is not a substitute for this step. Its sentinel edits affect `rz_repr`, `bfe_repr`, and `bodem_repr`; repository reconstruction established that `svat_repr` itself was unchanged, but the actual 10,242-row schema data are not currently materialized in this runtime.

## Revised blocker classification

The raster component of the previous blocker is resolved at semantic-content level.

Remaining blockers:
- raw 49-run realized archive is still not readable;
- exact persisted representative-SVAT table is not currently recoverable from the active Project/Library surface;
- exact `svat.asc` or another source-bound SVAT-to-cell relation is not currently recoverable from the active Project/Library surface.

Do not replace either missing authority with a newly computed HRU majority or with `Runs.col/row`: the latter are the legacy geographic representative location and are not proven to be Piet's hydrologic `svat_repr`.
