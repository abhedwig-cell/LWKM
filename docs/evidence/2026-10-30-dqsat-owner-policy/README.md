# dqsat owner policy restoration — 2026-10-30

Actual identified raster + current HRU CSV and membership: 427,656 SVATs,
10,242 HRUs. SWP server sampling and DRA preparation agree on every HRU;
medians additionally checked against NumPy. The population CSV is evidence,
not a production lookup: producers recalculate from their actual membership.

2,835 HRU medians differ from the representative source sample, including all
14 representative zeros. 515 zero member samples excluded; no member NoData.
Median dqsat spans 2–20 m; candidate drainage spacing L spans 8–80 m.
Compare representative, positive median and positive mean in summary.json.
The maximum relative median/positive-representative difference is 4.5 (+450%).

Reproduce with `python -m tools.qualify_dqsat_population --schema HRU.csv
--membership HRU_MEMBERSHIP.csv.gz --raster grensvlak_NHIWQ_v2_fill.asc
--output qualification_output` (one command line). Actual input SHA-256 values
are in summary.json. The server uses only stdlib + NumPy; this offline audit
also uses pandas. Local checks: 46 targeted tests passed, Python 3.12 / NumPy
2.3.5 / pandas 2.2.3. No new server execution or SWAP-response qualification
is claimed. The previously reported server environment is Python 3.10.8 /
NumPy 1.23.5; requalification on that environment remains a server task.

Server03 searches existing directories for the identified raster and records
all searched roots/candidates. Its current server location is not established
by this local audit. No `dqsat_svat.inp` equivalence is assumed. SWP and DRA
share tools/dqsat_policy.py; Work C cache fingerprints now include this module
and the coordinate sampler, invalidating previously prepared results.
