# Frank export v0.2: MODFLOW-laag-1-budgetten, directe NHI-serverproducer

Datum 4 november 2026. Aanvulling op `FRANK_DIRECT_NHI_PYTHON_PRODUCER_V01_20261104.md`.

## Verifieerbare upstream
Door projecteigenaar geleverd `manifest_1991_2020.zip`: de oorspronkelijke MetaSWAP-run over 1991–2020 is succesvol, 30 jaar/1080 decades, 645582 SVATs, 6 originele MetaSWAP-bronnen volledig. In het manifest zijn alleen `Neerslag`, `Evapotranspiratie`, `Oppervlakkige afstroming`, `SVAT` en `Opp_svat` gevuld; `Infiltratie` is nog leeg omdat de exacte ASC-bron niet op de gevonden locatie stond.

## Nieuwe pakketinhoud
In de actuele gebruikersconversatie als ZIP `LWKM_Frank_LHM_Server_v02_MODFLOW.zip` geleverd:
- `build_modflow_svat.py`, `wb01.py`, `wb03_balance.py`, `wb10_reader.py`, bestaande MetaSWAP-builder en tests;
- `CONTROLE_MODFLOW_2020.cmd`, `START_MODFLOW_PROEF_2020.cmd`;
- `CONTROLE_MODFLOW_KLIMAAT.cmd`, `START_MODFLOW_KLIMAAT.cmd`;
- `LEESMIJ_MODFLOW.md`.
Code **is nog geen git source commit**, maar lokaal synthetisch getest (2 SVATs met gecontroleerde m3/year, mm/year, bronstemmen, join; bestaande 36-decade-MetaSWAP-regressietest succesvol). Nog geen echte NHI-serveruitvoering van deze nieuwe module.

## Contract
Voor ieder gekoppeld SVAT worden op het oorspronkelijke 250x250m MODFLOW-celrooster afzonderlijke getekende fluxvolumes van laag 1 ingelezen:
`bdgqlat` (FRF+FFF), ongecorrigeerde `bdgflf`, `bdgwel`, `bdgghb`, `bdgdrn` (3 systemen) en `bdgriv` (4 systemen). Origineel teken positief naar laag 1. Eenheden: getekende m3/volledige cel/jaar en equivalente mm/jaar = volume*1000/62500; SVAT-oppervlak wordt NIET als deler toegepast. `QEXT4=QLAT+FLF+WEL+GHB`, `DRAIN_RIV=DRN+RIV`, uitsluitend diagnostische aggregaten. Geen qmodf.

Voor de 2020-proef extra 8 `bdgsto` en 8 `bdgbnd` partities uit originele `run_2020_2022`; geen onterecht 1991–2020 klimaatgemiddelde van slechts 2020-beschikbare STO/BND. Oorspronkelijke code `wb03_balance.py` wordt als source-bound reader hergebruikt, met eerder erkende conventie: geen package-stress buiten brondekking is nul en brondekking wordt apart gerapporteerd, QLAT is verplicht voor iedere gekoppelde cel.

De onafhankelijke MODFLOW-tabel `MF_SVAT_L1_YYYY_YYYY.csv` en `MF_manifest_YYYY_YYYY.json` komen onder `LWKM_run_resultaten_totaal/frank_export_modflow`. Alleen voor 1991–2020 kan dezelfde SVAT-id geverifieerd met oorspronkelijke `FRANK_LHM_SVAT_BASE_1991_2020.csv` gejoined worden; de MF-velden blijven expliciet afzonderlijke diagnostische kolommen. Dit is nog niet de fysisch volledige Frank-waterbalans: `Fldrou/Fldrin`, `Ontwatering`, rivierinfiltratie, kwel/vervanging en HRU-stappen mogen NIET zonder geverifieerd producentcontract rechtstreeks worden ingevuld vanuit DRN/RIV of FLF.

## Reproduceerbare serveruitvoering
Pak ZIP uit onder `LWKM_tools`; open CMD in `LWKM_Frank_LHM_Server_v02`; voer `CONTROLE_MODFLOW_2020.cmd`, daarna `START_MODFLOW_PROEF_2020.cmd` uit. Na teruggeleverde en geverifieerde `MF_manifest_2020_2020.json`: `CONTROLE_MODFLOW_KLIMAAT.cmd` en `START_MODFLOW_KLIMAAT.cmd`.

Alle nieuwe code leest bronbestanden alleen-lezen. Klant-specifieke reële uitvoer, bronpadbeschikbaarheid en performance moeten nog op NHI-server worden geverifieerd.
