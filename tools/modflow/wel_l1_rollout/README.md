# WEL-laag-1-uitrol, 1980-2025

Deze map bevat de PowerShell/.NET-uitrolcode voor **geschatte** historische WEL-fluxen op MODFLOW-laag 1. Zie de [technische notitie](../../../docs/server/LWKM_MODFLOW_WEL_L1_RECONSTRUCTION_AND_ROLLOUT_2026-10-16.md) voordat je resultaten interpreteert.

De uitvoer is **niet gelijkgesteld aan de originele MODFLOW-WEL-uitvoer**. Het eind-1979-raster wordt vastgehouden behalve voor zeven eerder onderzochte, tijdsafhankelijke winningcellen.

Benodigd naast de gecommitte bestanden:
- `variabele_cellen_1980_2025.csv` uit de eerder uitgegeven ZIP `LWKM_WEL_L1_1980_2025_UITROL.zip`, **niet in Git** (dagelijks 7 voorspellingen);
- `bdgwel_19791231_l1.idf` in de bestaande `LWKM_run_resultaten_totaal\modflow\bdgwel`-map, **niet in Git**.

`anker_19791231.csv` is hier gecommit als transparant invoeranker van zeven cellen; de getallen zijn afkomstig uit het uitrolpakket. Dit is geen onafhankelijke kwalificatie van die bronwaarden.

Proef (PowerShell via CMD):
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_wel_l1_1980_2025.ps1" -Start 1980-01-01 -End 1980-01-03
```

Uitrol:
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_wel_l1_1980_2025.ps1" -All
```

Standaard wordt bestaande uitvoer niet overschreven. Houd statuslog, exacte invoerbestanden en checksums bij iedere serverrun.
