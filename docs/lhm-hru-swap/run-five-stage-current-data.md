# Uitvoeren van de huidige vijfstappenreconstructie

De huidige analyse kan rechtstreeks op de reeds aangeleverde archieven worden uitgevoerd zonder eerst handmatig bestanden te kopiëren of hernoemen.

## Benodigd

- `csv.zip`
- `LHM2SWAP.zip`
- Python met de dependencies uit `tools/requirements-lhm-hru-swap.txt`

## Commando

```bash
python tools/run_current_data_reconstruction.py \
  --csv-zip /pad/naar/csv.zip \
  --lhm2swap-zip /pad/naar/LHM2SWAP.zip \
  --out results/HRU10242-current
```

De runner zoekt de benodigde bestanden in de ZIP-archieven, extraheert alleen de benodigde leden naar een tijdelijke stagingmap, berekent SHA-256-checksums en roept daarna de QA-tool aan.

## Hoofduitvoer

- `archive-inventory.json`: exacte archive members + checksums;
- `effective-HRU10242-current.json`: feitelijk gebruikte config;
- `stage_hydrology.csv`: S0/S1 en huidige keten per hydrologische variabele;
- `domain_effect.csv`: S0 → S1;
- `correction_diagnostics.csv`: onder andere `kwel_org → kwel`;
- `qualification_counts.csv`: aantallen per kennisregel;
- `qualification_overlap.csv`: overlap tussen regels;
- `hru_mapping_summary.csv`: donorwisselingen versus flags;
- `representation_effect.csv`: donor/representatieve-SVAT effecten;
- `hru_average_backprojection.csv`: landelijke S3 → S4-maat voor GHG en NettoKwel;
- `hru_average_backprojection_detail.csv`: SVAT-voor-SVAT delta;
- `hru_average_backprojection_by_region.csv`: regionale samenvatting op `LDGBclus_orig`;
- `qa_summary.json`;
- `report.md`.

## Belangrijke interpretatie

De backprojection gebruikt voor het pure HRU-effect de exacte clusteringvariabelen uit de actuele HRU-koppeltabel:

- `GHG_LHM43_orig → GHG_average`;
- `NettoKwel_LHM43_orig → NettoKwel_average`.

Daarmee wordt vermeden dat een vergelijkbaar maar semantisch niet exact bewezen veld uit de algemene SVAT-tabel wordt gebruikt.

De Flevoland-uitvoer blijft voorlopig diagnostisch zolang de alternatieve LHM-run en alle mee veranderende balanscomponenten niet formeel zijn gebonden.
