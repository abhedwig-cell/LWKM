# Frank-export: directe NHI/LHM Python-proefketen v0.1

Datum: 4 november 2026. Projecteigenaarbesluit: niet terugzoeken naar oude SVAT-info-CSV's als primaire bron. Produceren uit oorspronkelijke LHM/MetaSWAP/MODFLOW-bronbestanden op NHI-server, met Deltaforge Python `E:\tools\deltaforge\deltaforge_4\python.exe`. Zelfstandige EXE niet nodig.

## Geleverde software
In de lopende gebruikersconversatie is `LWKM_Frank_LHM_Server_v01.zip` als concreet pakket gebouwd, syntactisch gevalideerd en met 2 SVATs × 36 synthetische decadische datasets getest. Het pakket bevat:
- `build_svat_base.py` met hoofdverwerking op echte LHM-bronnen;
- onveranderde eerder gebruikte `wb10_reader.py` (area_svat- en IDF-parser);
- `CONTROLE_BRONNEN.cmd`, `START_FRANK_PROEF_2020.cmd`, `START_FRANK_KLIMAAT_1991_2020.cmd`;
- `test_server.py`, `LEESMIJ.md`.
Broncode zit **in dit stadium in het downloadbare ZIP, niet via deze documentatie in een Git source tree**. Eerst echte NHI-kwalificatie, daarna opnemen in versioned `tools` op de relevante integratiebranch.

## Door gebruiker bevestigde Frank-velddefinitie
`Infiltratie = totale rivierinfiltratie`; in historische v0.20 schema heet deze bronindicator `wegzijgingz(mm/j)`, via `Riv_infiltratie_1991-2020_sum.asc`. Interpretatie bronperioden en onderliggende systemen bij echte bronbinding toetsen. `Fldrin345` = som systemen 3, 4, 5. `GG` = gemiddelde grondwaterstand, nooit (GLG+GHG)/2. `Dynamiek=GLG-GHG`. Onbekend: `Indicator vervangen Svats`, `N ???`.

## Wat v0.1 daadwerkelijk kan
SVAT basis uit `area_svat.inp` (SVAT-id, oppervlak, xy) plus 6 originele MetaSWAP-decade-IDFs: `bdgpm`, `bdgetact`, `bdgqrun`, `bdgdecstot`, `bdgpssw`, `bdgpsgw`. Jaarlijk cache met source-stat signature (name, size, mtime), geen per-IDF hash. Voor de gebruiker gevraagde kolommen vult deze proef **alleen**: identiteit, area, neerslag (bdgpm), evapotranspiratie (-bdgetact), runoff (-bdgqrun) als gemiddelde mm/jaar. Infiltratie alleen bij exacte 1991–2020-rivierinfiltratie-ASC onder gepreconfigureerde bronlocatie. Alle overige velden blijven leeg met `dekking_per_veld` en machineleesbaar manifest. Oorspronkelijke signed rastertermen in aparte diagnostische CSV, geen `qmodf` of `STO` ingemengd.

2020 pilot: 36 decades; klimaat 1991–2020: 1080 decades. Volledige NHI-server-run nog niet uitgevoerd. Open source- en kwalificatievragen: originele landgebruik/bodem/GT/GHG/GLG bronnen, bronuitvoer drainage en infiltratiesystemen, beregening, donorvervanging en 7 logisch onderscheiden verwerkingsstappen; kolomperioden en oppervlaktebasis. Niet onterecht claimen dat alle 39 velden nu geproduceerd zijn.

## Aanvaarding en vervolgstap
1. Voer `CONTROLE_BRONNEN.cmd` uit vanuit uitgepakte toolsmap; bevestig alle benodigde source-decade-IDFs.
2. Voer `START_FRANK_PROEF_2020.cmd` uit; controleer `manifest_2020_2020.json`, velddekking, ID/oppervlakaantallen en signed hydrologie.
3. Indien correct: `START_FRANK_KLIMAAT_1991_2020.cmd`. Controle op consistentie van LHM-outputperiode (1991–2020).
4. Daarna originele specifieke IDF- en MetaSWAP-invoerbronnen voor resterende Frank-velden koppelen en aparte kwantificeerbare logische stappen implementeren. Geen impliciete nulvulling of vervanging door toevallige oude CSV-bestanden.
