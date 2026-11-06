# LWKM Frank: geconsolideerde productieketen v0.1 (2026-11-06)

**Doel**: de ad-hoc Frank-exportpakketten vervangen door één begrijpelijke, herhaalbare operationele entrypoint met dezelfde bestaande numerieke producenten, niet direct een fysisch nieuwe procedure. De bestaande ongecorrigeerde SVAT-basistabel draait momenteel nog op de NHI-server, dus oude runs/output ongewijzigd laten.

Werkelijk gebouwd ZIP-artifact: `LWKM_Frank_Pipeline_v01.zip`. Bronnen in hetzelfde pakket: `frank_pipeline.py`, `pipeline_config.json`, negen zelfstandige rekenmodules, één gedeelde byte-identieke `wb10_reader.py`, `wb01.py`, `wb03_balance.py`, volledige gekwalificeerde bodemlookup en landgebruiklookup, ECHO 66-gebieden-raster, source-hash manifest, `test_pipeline.py`, `LEESMIJ.md`, plus drie CMD entrypoints.

## Enige uitvoercommando's vanuit de map onder LWKM_tools

- `CONTROLE_FRANK.cmd`: snelle lijst met aanwezige outputs, geen zware rasterlezing; status is **niet** uitvoerkwalificatie.
- `START_FRANK.cmd`: gecontroleerde keten, per stap bestaande CSV 645582 unieke SVAT-IDs en verplichte velden verifiëren; volledig valideren en hergebruiken, ontbrekende producer uitvoeren volgens afhankelijkheden; **nooit een bestaand onvolledig uitvoerbestand automatisch overschrijven**, omdat bestaande run nog actief kan zijn.
- `TEST_FRANK.cmd`: syntax/CLI/contract regressie zonder NHI-gegevens.

`frank_pipeline.py verify`: alle outputs inhoudelijk op ID/kolommen/aantal controleren zonder een producer te starten. Centrale status `LWKM_run_resultaten_totaal/frank_export_pipeline_v01/PIPELINE_STATUS.json` vermeldt script-hashes en per stap hergebruik/producer status. Door adoptie van legacy uitvoer is historisch volledige bron-naar-uitvoer-reproduceerbaarheid **nog niet aangetoond**; oorspronkelijke producentmanifesten blijven nodig.

## Stappen (vaste afhankelijkheden)

`msw_basic` -> originele getekende zes MetaSWAP-termen en tabel; `modflow_original` -> 16 oorspronkelijke bruto laag-1-fluxen; `gxg` -> GHG/GLG uit halfmaandelijkse heads; `gw_percentielen` -> GW5/GW95; `et_componenten` -> Tact Eic Ebs Epd Esp en beregening; `statisch_gt` -> fixed-width area_svat, lookups, Gt; `gebied_n` -> ECHO region, N=1; `qmodf` -> decadische qmodf; `svat_basis` -> oorspronkelijke ongecorrigeerde Frank SVAT tabel. Elke bronmodule staat nu één keer in een root-map, niet meer verspreid over losse ZIP's; gedeelde reader heeft één byte-identieke versie (SHA256).

Hoofd-output is ongewijzigd:
`LWKM_run_resultaten_totaal/frank_export_eindtabel/svat_basis_ongecorrigeerd_v01/FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv`.

Bewuste scope: geen Flevoland-correctie of RIV1-nettoherverdeling; geen donorvervanging/uitsluiting/HRU/SWAP. Gebied-NoData 88581 leeg is geaccepteerd; QmodF helper; geen MF-storage in overall diagnose; originele volle-MODFLOW-celoppervlakte 62500m2.

## Kwalificatie en ontbrekende architectuurwerk

Lokaal: `test_pipeline.py` PASS: negen producer-CLI's, afhankelijkheden, ID/kolomschema, NODATA; alle code `py_compile` PASS; ZIP-integriteit OK. Er is **nog geen serveruitvoering van de geconsolideerde controller**. Dit is een *operationele bundeling*, nog geen volledige broncode-herarchitectuur. Alle oorspronkelijke producenten gebruiken op plaatsen nog ingebouwde vaste NHI-paden. De controller weigert daarom ongecontroleerde wijziging van het werkruimtepad en maakt expliciet onderscheid tussen statuscontrole en volledige ID-validatie. Noch rekenmodule-fingerprint noch input-bronhashes zijn overal al uniform. Die punten vormen de eerstvolgende gerichte refactoring, pas na referentie-CSV-hash/regressie tegen huidige output.

Code zelf is via geteste ZIP geleverd; dit Git-document is geen claim dat de complete bronboom al in Git is ingecheckt. De volgende Git-integratie moet de broncode onder `tools/frank/` versioneren, reference manifests incorporeren en per module de hardcoded paden verwijderen met regressiebehoud.
