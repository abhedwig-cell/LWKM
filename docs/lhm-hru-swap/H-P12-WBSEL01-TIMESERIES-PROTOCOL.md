# WBSEL01 time-series evaluation criteria

For each supplied paired head snapshot compute corrected-minus-historical QBOT2 for all 10,242 HRUs.

Report per snapshot:
- mean, median, std;
- p01/p05/p95/p99;
- max absolute delta;
- counts above 0.01, 0.1 and 1 cm/day.

Report per HRU across snapshots:
- mean delta;
- mean absolute delta;
- maximum absolute delta;
- sign persistence;
- number/fraction of snapshots above thresholds.

Inspect:
- top 25 by maximum absolute delta;
- top 25 by mean absolute delta;
- HRUs where delta sign reverses;
- HRUs with >1 cm/day repeatedly.

The purpose is impact characterization, not deciding that a large delta is physically wrong. The semantic defect is already independent of delta magnitude.
