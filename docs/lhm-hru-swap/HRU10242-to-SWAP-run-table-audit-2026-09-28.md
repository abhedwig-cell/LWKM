# HRU10242 → SWAP run-table audit — 28 September 2026

Status: **OBSERVED OUTPUT CONSISTENT WITH v0.38**

Source artifact: supplied `csv.zip/SVAT2SWAP10242.csv`.

## Shape

- rows: 10,242;
- unique `run_id`: 10,242;
- `run_id` range: 1–10,242;
- all `scenario_id = direct`.

## Period

All rows contain:

- `TSTART = 1971-01-01`;
- `TEND = 2021-12-31`.

This confirms that the generated SWAP case table uses the 1971–2021 simulation period from the bound production control. This does not mean every upstream hydrological statistic has the same period: the control/source also references 1991–2020 flux products and 1980–2019 GHG/GLG products. Those periods must remain explicit provenance metadata rather than being collapsed into one generic “model period”.

## v0.38 rule checks

The source-derived rule

```
SWBBCFILE = 0 if SWBOTB == 7 else 1
```

holds for all 10,242 rows.

Observed bottom-boundary classes:

- SWBOTB 1: 1,121 HRUs;
- SWBOTB 2: 8,906 HRUs;
- SWBOTB 3: 208 HRUs;
- SWBOTB 7: 7 HRUs.

Thus:

- SWBBCFILE 1: 10,235;
- SWBBCFILE 0: 7.

Other observed ranges are compatible with the source/control mapping:

- `PONDMX = 5.0` for all rows;
- `RSRO = 0.5` for all rows;
- `tempBot = 9.0` for all rows;
- `SWINCO = 2` for all rows;
- `NUMNODNEW = 43` for all rows;
- `GWLI <= 0` throughout, consistent with the source clamp `MIN(0,...)`.

## Interpretation

Together with the embedded binary identity in `HRU2SWAP.exe`, these checks provide strong evidence that the supplied 10,242-row run table was produced by the bound HRUlist2SWAP v0.38 production path.

This does not yet prove that the generated per-HRU BBC/DRA/MET/SWP files are complete or that all 10,242 SWAP simulations were subsequently executed successfully.
