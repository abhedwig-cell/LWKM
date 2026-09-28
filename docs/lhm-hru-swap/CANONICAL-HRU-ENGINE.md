# Canonical HRU engine decomposition

Status: implementation started.

The historical R source is decomposed into explicit modules rather than translated line-for-line.

1. input authority: selected SVAT state + qualification + LDGB mapping;
2. primary cluster builder: eleven source-bound aggregation/relaxation rounds;
3. rest assignment round 1: weighted nearest donor within LDGB x lu4;
4. rest assignment round 2: weighted nearest donor within LDGB x lu2;
5. HRUextra builder for unresolved remainder;
6. HRU representative selector;
7. HRU/NRU schema writer;
8. SVAT backprojection QA.

Implemented now in tools/hru_core.py:

- weighted donor distance with square-root weight scaling;
- nearest donor selection;
- representative existing-SVAT medoid core;
- area-weighted backprojection bias/MAE/RMSE.

The primary eleven-round cluster builder is deliberately not guessed from summary documentation. It remains the next implementation unit and must be transcribed from the exact bound R source with round-by-round regression fixtures.

The canonical engine must emit separate tables for membership, cluster donor and representative SVAT. Raster exports are derived compatibility products and cannot overwrite each other.
