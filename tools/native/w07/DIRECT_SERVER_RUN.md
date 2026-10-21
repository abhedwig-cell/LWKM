# W07 NHI raw-source to DRA (experimental)

One standalone Windows executable consumes the uncompressed original LHM IDF grids and AHN ASCII, the SVAT-to-HRU relationship, representative dqsat authority, HRU horizon counts, and H1 monthly IDFs. It produces DRA candidates and a source-status register, without Python on the NHI server.

Command:

```cmd
W07Dra.exe --from-raw raw_config.json W07_NATIVE_DRA_OUT
```

Mandatory `raw_config.json` keys:
- `members_csv`: SVAT-HRU source relation with columns svat,hru,x,y.
- `dqsat_csv`: qualified original representative-SVAT HRU dqsat mapping, columns hru,representative_dqsat.
- `horizons_csv`: original qualified HRU SWAP soil-horizon counts, columns hru,n_horizons.
- `ground_asc`: original `ahn_f250_cm.asc` in centimetres.
- `H1_monthly_dir`: original `peilh_YYYYMMDD.idf` monthly sources.
- `start_year`, `end_year`: SWAP simulation boundaries.
- Each raw IDF path: `H1_cdr`=COND_HL1_250.IDF, `H1_bottom`=both.idf, `H1_inf`=infmz_h_250_l1.idf; `P/S/T_cdr`=COND_primair/secundair/tertiair.IDF, `P/S/T_inf`=inf_mz_primair/secundair/tertiair.IDF, `P/S/T_sum`=PEIL_P1Z/S1Z/T1Z_250.IDF, `P/S/T_win`=PEIL_P1W/S1W/T1W_250.IDF, `P/S/T_bottom_sum`=BODH_P1Z/BODH_S1Z/PEIL_T1Z_250.IDF and `P/S/T_bottom_win`=BODH_P1W/BODH_S1W/PEIL_T1W_250.IDF. `MVG_cdr`=COND_greppels.IDF; `MVG_bottom`=BODH_BRP2012_MVGREP_250.IDF; `PIPE_cdr`=COND_buisdrainage.IDF; `PIPE_bottom`=BODH_B_250.IDF; `OLF_cdr`=COND_SOF_250.IDF; `OLF_bottom`=BODH_SOF_250.IDF.

**These source filenames come from the Work C2 Python authority. Exact uncompressed source directories on NHI are not yet verified.** The code does not invent paths.

Current status: Native raw-reader, static SVAT/HRU aggregation, monthly H1 interpolation, automatic five-level fitting, method-3 serializer, and per-HRU error log exist in experimental code. Two qualified static mapping tables (representative dqsat, soil horizon count) are currently required; they are not precomputed drainage records. A full direct-source numerical comparison to C2, especially seasonal source coverage and error tolerances, is **not** complete. Do not claim 10242 DRA files or scientific admission until actual source-run + C2 comparison + SWAP 4.3.1 models pass. Keep output directory versioned and immutable.
