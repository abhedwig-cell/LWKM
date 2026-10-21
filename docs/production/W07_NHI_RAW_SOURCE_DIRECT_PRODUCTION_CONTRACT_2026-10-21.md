# W07 NHI raw-source direct production contract (owner decision 2026-10-21)

**Requested final behavior:** run one offline Windows CMD/EXE against the **original LHM 4.3.3 server-side source files** and write the DRA files for **all 10,242 HRUs**. Requiring upstream Python or a separately generated renderer-catalogue is **not** an acceptable final implementation.

## Stages within the same NHI-server executable

1. Read and authenticate the LHM static IDF grids and monthly H1 stage IDFs directly under server-side LHM source directories; read the authoritative SVAT->HRU relation, HRU schema, and original representative-SVAT dqsat source. Honor each individual IDF NODATA sentinel, grid alignment and original elevation/depth sign.
2. Aggregate all 427,656 SVAT members into seven physical system records per HRU: H1, P, S, T, MVG, PIPE and OLF, including drainage and infiltration conductances, summer and winter stages, dynamic H1 monthly stage profiles, drainage bottom and spacing L=4*dqsat.
3. Apply owner rules at physical level: DRARES >100000 omit source, INFRES >100000 disable infiltration, missing H1 factor => disable only that cell's infiltration. Preserve source and correction audit.
4. If >5 active systems, run the automatic five-level hydraulic equivalent fitter within this executable. Keep pipe-specific SWAP semantics, preserve conductance where possible, quantify net, drainage and infiltration errors. Never reject solely because of >5 systems, but never fabricate invalid/missing source inputs.
5. Render true SWAP 4.3.1 method-3 DRA files per HRU; input profile horizon count must come from the qualified source/hydrological model context, not be guessed. Serialize dynamic H1 stages for complete simulation years.
6. Record per-file SHA-256, original IDF/source identity, fitted source lineage, transformations, output and scientific/error status; support verified resume with versioned immutable products. Reuse the 10,213 previously qualified bytes or validate discrepancies with original C2 by byte and numerical comparison.
7. Run comparative qualification against C2: 10,213 original DRA files (exact bytes where applicable), 29 previously blocked candidates and SWAP 4.3.1 model runs covering physical extremes.

## Current implementation and gap

PR #20 provides a tested native Windows SWAP DRA **renderer** of a prebuilt catalogue. Commit 63c6bdf adds the genuine LHM IDF binary reader and IDF inspection entry point, which is the first raw-data component. **The complete raw raster aggregation, seven-physical-system producer and native fallback optimizer are NOT yet implemented**. It is not correct to describe PR #20 as accomplishing the owner target. Native Windows tests and comparisons must be extended to real source grids, not only synthetic render smoke.

The older Python sources in the repository are scientific oracles: `tools/diagnose_dra_10242.py`, `tools/work_c2_drainage.py`, `tools/dra_owner_policy.py`, `tools/dra_level_compression.py`, `tools/dra_protected_compression.py`, `tools/generate_dra.py`.

The exact source tree, source and schema checks must be discovered from these authorities. Avoid treating historical compressed Q4 ZIPs as the server production source when the same original files exist uncompressed. The native program must take qualified, explicit root paths/configuration and no hidden local file references.
