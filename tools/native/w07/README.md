# W07 standalone Windows drainage renderer

Self-contained Windows x64 EXE. This is the **DRA serialization stage** of migration, not a replacement for the scientific LHM raster / SVAT aggregation. It consumes a versioned `renderer_catalogue.json` with full SWAP-ready level metadata, built from Work C2 full HRU checkpoints and SWP horizon counts. It renders no more than 5 levels and logs source errors without inventing missing values. No Python or installed .NET on NHI server. The scientific seven-to-five fallback is in Python upstream and must be ported separately if *all* raw-source derivation is to move onto NHI.

Each item: {"hru":7876,"n_horizons":4,"levels":[{"drnres":100,"infres":1000,"dd":40,"dep":1.5,"peil_sum":0.8,"peil_win":1.0,"medium":"open_channel","allow_infiltration":true,"level_series":null}]}. Top-level: schema_version=1,start_year=1971,end_year=1972,hrus=[...].

Do not claim a scientifically qualified 10242-HRU run until the real source catalogue, SWAP parser and execution tests pass.
