# Frank SVAT/HRU vergelijkings-export, uitvoeringsvoorwerk v0.2

Datum: 4 november 2026. Afgesproken: zoveel mogelijk voorbereiden vóór overleg met Frank en Leo.

## Beschikbaar prototype in deze gebruikersconversatie
`LWKM_Export_Frank_v02.zip` (gegenereerd en lokaal op synthetische data getest). Inclusief:
- `export_frank.py`: stapsgewijze SVAT-export vanuit bestaande 75-koloms `LWKM_makeHRU`-CSV's; optionele HRU-oppervlakteweging met oplopend geaggregeerde totalen (geen alle-SVAT-geheugentabel);
- `compare_stages.py`: verschillen in gedeelde numerieke velden voor **aangrenzende en daadwerkelijk aanwezige** logische stappen, geen zelf aangemaakte stappen;
- `inventory_sources.py` en `CONTROLE_BRONBESTANDEN.cmd`: beperkte, read-only inventaris op de bekende serverlocaties; bronkandidaten niet automatisch goedkeuren;
- `run_stages.py` + `START_FRANK.cmd`: serverlauncher via bestaande Deltaforge Python;
- `tests.py`: regressies op synthetische data.

De broncode is in dit stadium geleverd als ZIP op de conversatie, **niet** op basis van deze notitie geclaimd als gecommitte softwarebron in Git. De volgende integratiesessie kan ZIP-code onder een versioned tools path toevoegen wanneer de test tegen de reële SVAT/HRU-stapsnapshots slaagt.

## Expliciet vastgelegde veldbesluiten
- `Fldrin345 = aanvoer_sys3+aanvoer_sys4+aanvoer_sys5` (mm/j).
- `Dynamiek=GLG-GHG` (cm, beide dezelfde periode en onder-maaiveld-referentie).
- `GG` is echte gemiddelde grondwaterstand, **niet** `(GHG+GLG)/2`; vereist bronkolom via optionele mapping.
- `Infiltratie` blijft leeg tot semantisch eenduidige bron is gekozen. Oude `wegzijgingz(mm/j)` representeert specifiek rivierinfiltratie-indicator, niet automatisch alle infiltratie.
- `Indicator vervangen Svats` moet afgeleid worden uit expliciete vervangingsrelatie en is niet dezelfde kolom als `svat_donor`, `isverdacht` of `islwkm`; `N ???` nog open.
- HRU-aggregatie is area-weighted diagnostic, niet de officiële representatieve HRU-toestand.

## Aanvaardingscriteria voor echte productie
1. Genereer read-only `broninventaris.csv`, koppel elk werkelijk source-CSV-snapshot aan exact één goed gedefinieerde stap, verifieer hash.
2. Test 75-koloms productietabel op parser, decimalen, 645582 oorspronkelijke SVATs en afwijkingen; maak geen populatieclaim tot run.
3. Verifieer bron/perioden, eenheden en waargenomen velden met Frank/Leo.
4. Draai alle werkelijk beschikbare logische stappen zonder overschrijven van source; vergelijk SVAT-ID set, aantallen en aggregatie-oppervlak.
5. Valideer HRU-koppeltabel en representativiteit expliciet.
6. Pas na daadwerkelijke server-run en wetenschappelijke check een definitieve kolomvolgorde vaststellen, versioned schema en producer/admission commit.

## Herkomst
Source-bound schema: `schemas/svat/LWKM_makeHRU-v020.md`; eerdere contractnotitie `FRANK_STAGE_COMPARISON_EXPORT_CONTRACT_20261104.md`; aanvullende besluiten `FRANK_EXPORT_FIELD_DECISIONS_20261104.md`.
