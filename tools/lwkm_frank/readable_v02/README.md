# Frank SVAT leesbaar v0.2

12 november 2026. Projecteigenaar verzoekt echte GLG/GHG naast GW5/GW95 en mm/jaar op MetaSWAP-oppervlak naast de m3-kolommen. Dit is een aanvullende read-only naverwerkingsstap. Geen modelrun, geen GxG-herberekening, geen verandering van historische hydrologische waarden of geregistreerde legacy-modules.

## Diagnose uit de oorspronkelijke code

Onderzocht: `tools/lwkm_frank/legacy/maak_svat_basis.py` op commit `b06e8d576f1ced10eece35c792165b656b0a8213`, blob `ec1ee5c9b578fd9e86109e4aa1e4f3072476e85a`.

SCHEMA en row_calc schrijven GLG/GHG naar de eindtabel. AUDIT bevat GW5/GW95 maar geen GLG/GHG. De 16 MODFLOW-m3-velden in de audit zijn totalen over 30 kalenderjaren (1991 tot en met 2020); de eindtabel converteert ze al met 1000/(62500*30). De server-CSV is in deze sessie niet rechtstreeks geopend. Dit verschil tussen de twee schema's is dus een codebevinding, geen nieuwe serverwaarneming.

## Uitvoeren

Pak het geleverde pakket uit onder `G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools`. Open CMD in de map waarin START_FRANK_LEESBAAR.cmd staat en voer uit:

```cmd
START_FRANK_LEESBAAR.cmd
```

Gebruikt de bestaande `E:\tools\deltaforge\deltaforge_4\python.exe`, alleen standaardbibliotheek (Python >=3.8). Geen installatie. Een andere bestaande interpreter kan via LWKM_PYTHON worden aangewezen.

De bronnen zijn de bestaande eindtabel, controletabel, GxG/percentielentabel en MANIFEST_FRANK_SVAT_BASIS.json. Exacte standaardpaden staan in DEFAULTS in het script. Bronhashes moeten overeenkomen met het oorspronkelijke manifest. Alle 645582 SVATs moeten uniek aansluiten. De bronvolgorde hoeft niet gelijk te zijn.

Nieuwe uitvoer onder `LWKM_run_resultaten_totaal\frank_export_eindtabel\svat_leesbaar_v02`:

- FRANK_SVAT_LEESBAAR_1991_2020.csv: puntkomma, decimale komma, UTF-8 BOM, drie decimalen voor berekende waarden, eenheden en oppervlaktebasis in de koppen.
- FRANK_SVAT_COMPLEET_TECHNISCH_1991_2020.csv: dezelfde kolommen, decimale punt en volledige float64-berekeningsprecisie.
- FRANK_SVAT_CONTROLE_UITGEBREID_1991_2020.csv: alle oorspronkelijke auditkolommen/waarden, echte GLG/GHG en aanvullende volume-/dieptekolommen naast de m3-velden.
- KOLOMMEN_EN_EENHEDEN.json en MANIFEST_FRANK_LEESBAAR_V02.json: definities, bronnen en hashes.

Een bestaande uitvoermap wordt niet overschreven. Nieuwe uitvoer wordt pas gepubliceerd na volledig geslaagde verwerking. Een tijdelijke SQLite-werkdatabase houdt geheugengebruik beperkt; voldoende vrije schijfruimte is nodig. Bronnen blijven onaangeroerd.

## GxG

GHG en GLG komen uitsluitend uit GHG_cm_mv en GLG_cm_mv van de bestaande GxG-bron en worden gedeeld door 100 voor m beneden maaiveld. GW5 en GW95 blijven afzonderlijke statistieken. Geen vervanging door percentielen, ook niet bij ontbrekende bronwaarden. Ontbrekende bron-GxG stopt de verwerking. Lege of ontbrekende GxG in de eindtabel wordt aangevuld; conflicterende geldige waarden worden niet stilzwijgend overschreven.

De bestaande 14e/28e-bron wordt hergebruikt. GG=(GHG+GLG)/2 volgens het projectbesluit van 6 november; Dynamiek=GLG-GHG. Het oude afzonderlijke GG_14_28_gemiddeld_cm_mv blijft in de controletabel behouden en is een andere statistiek.

## Oppervlakte en tijd

Voor oorspronkelijke MODFLOW-periodevolumes V (m3 over 30 jaar):

```text
m3/jaar = V/30
mm/jaar MFcel = 1000*V/(30*62500)
mm/jaar MSW-equivalent = 1000*V/(30*Opp_svat_m2)
```

MSW-equivalent is dezelfde volledige MODFLOW-celhoeveelheid uitgedrukt op MetaSWAP-oppervlak, GEEN proportionele volumetoedeling aan de SVAT en GEEN nieuwe fysische SVAT-flux. De oorspronkelijke celbasis blijft daarnaast beschikbaar. Meerdere SVAT-rijen kunnen dezelfde volledige MF-celhoeveelheid presenteren; die mogen niet voor landelijke volumes worden opgeteld.

Voor MetaSWAP: m3/jaar = oorspronkelijke mm/jaar * Opp_svat_m2/1000. Hoeveelheden die al per jaar zijn worden niet nogmaals door 30 gedeeld, ook het bestaande overall_volume_m3_per_j_cel niet. Tekens blijven onveranderd.

In de uitgebreide audit blijven oorspronkelijke veldnamen met alleen _m3 staan: deze zijn uitdrukkelijk 30-jaarstotalen. De extra kolommen benoemen de jaareenheid expliciet. De leesversie gebruikt uitsluitend expliciete jaar- en oppervlakte-eenheden voor fluxen.

De MSW7-som en het overall onverklaarde saldo blijven diagnostische grootheden; deze wijziging bewijst geen volledige waterbalanssluiting en verandert geen BBC-, Flevoland-, donor- of HRU-keuze.

## Verificatie

29 synthetische unittest-tests lokaal geslaagd: GxG los van percentielen, ontbrekende GxG-kolommen, afwijzen ontbrekende bron-GxG, eenheden, factor 30, signed volumes, oppervlakken, behoud auditwaarden, joins, hashafwijkingen, Nederlandse CSV-notatie en afbreken zonder publicatie. Uitvoeren in deze map: `python -m unittest -v test_frank_leesbaar`.

Geen uitvoering op de echte 645582 serverrijen in deze sessie. De Windows-CMD is niet op Windows getest. Productievrijgave van de bredere pipeline blijft ongewijzigd.
