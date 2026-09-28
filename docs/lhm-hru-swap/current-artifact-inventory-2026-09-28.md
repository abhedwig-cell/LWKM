# Current HRU10242 artifact inventory — 28 September 2026

Status: **OBSERVED ARTIFACT SET**

The supplied `csv.zip` contains 13 top-level current HRU10242 artifacts.

| artifact | rows | role |
|---|---:|---|
| `SVAT_INFO_HRU.CSV` | 427,656 | current SVAT information table |
| `export_svat_HRU_NRU_10242.csv` | 427,656 | SVAT→HRU/NRU relation |
| `export_HRUschema_10242.csv` | 10,242 | authoritative observed HRU schema |
| `export_HRUschema_10242_copy.csv` | 10,242 | copy used by HRU2SWAP control |
| `export_NRUschema_10242.csv` | 25,054 | NRU schema |
| `HRUAFV.CSV` | 10,242 | HRU discharge diagnostic |
| `SVAT2SWAP10242.csv` | 10,242 | HRU2SWAP generated SWAP run table |
| `HRU10242.csv` | 10,242 | HRU summary artifact |
| `HRU10242_sel.csv` | 10,242 | selected/geographic HRU artifact |
| `export_svat_HRU_NRU_10242_out.csv` | 427,656 | downstream/output variant of relation |
| `SVAT_INFO_HRU_out.CSV` | 427,656 | downstream/output variant of SVAT table |
| `hrunrulist.csv` | 427,656 | HRU/NRU list |
| `LHM4.3.3_HRU10242_2026-06-11.csv` | 10,242 | dated HRU10242 product |

## Immediate implications

1. `SVAT2SWAP10242.csv` confirms that HRU2SWAP was actually executed for the current 10,242-HRU configuration; it is not merely inferred from source/control.
2. `export_HRUschema_10242_copy.csv` and `export_HRUschema_10242.csv` have the same row count and must be content-reconciled before treating the copy as an independent authority.
3. The supplied current artifact bundle stops at the SWAP **run-table/input-generation boundary**. It does not contain the large SWAP time-series/result package or an obvious postprocessing summary produced from completed SWAP runs.
4. Therefore SWAP execution/postprocessing authority cannot be inferred from `csv.zip` alone.

The next downstream evidence target is the actual SWAP run/postprocessing package or the script on Leo that reduces completed SWAP outputs to the LWKM summary CSV.
