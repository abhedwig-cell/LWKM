# LWKM Frank: gecorrigeerde SVAT-kandidaat, 16 november 2026

De gecorrigeerde uitvoer van 1991-2020 voor 645.582 originele SVAT's is als **kandidaat-referentie op tabelniveau** aanvaard uit het aangeleverde serverrapport `GXG_CORRECTION_CHAIN_V04.json`. De werkelijke nieuwe CSV is niet naar deze sessie gekopieerd; daarom blijft de oorspronkelijke uitvoerhash een gerapporteerde servercontrole, niet een onafhankelijk opnieuw gecontroleerd bestand. Zie `evidence/production/frank_v04_corrected_svat_candidate_20261116.json`.

## Ongewijzigd projecteigenaarbesluit

Voor GxG en afhankelijke producten is de enige maaiveldautoriteit de run-lokale `run_1970_1979/metaswap/area_svat.inp` (SHA256 `352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc`). De algemene `E:/LHM_4.3.3/Data/2_Model_Input/metaswap/inp/area_svat.inp` is geen bron voor nieuwe berekeningen.

De historische eindtabel (`7ec5b7bf...`) blijft ongewijzigd als auditbron, maar is geen numerieke GxG-acceptatie-oracle: 98 SVAT's hebben daarin een onjuiste maaiveldreferentie. De gecorrigeerde uitvoer heeft de gemelde SHA256 `31a5e7cb5c4939eea81971bd0e5fdf1a4a6820ea8b057ee81bb45b869697b614`. Ook GW5/GW95 en statische GT zijn opnieuw berekend. ET, Gebied/N en QModF zijn byte-identiek aan de oorspronkelijke tabellen; DRN-audit eveneens.

## Waterbalans: expliciet niet vrijgegeven

De in WB23 gedefinieerde oorspronkelijke diagnostische termensom op **eenduidige MODFLOW-celondersteuning** is:

`R0 = bdgdecstot + bdgpm + bdgpssw + bdgpsgw + bdgetact + bdgqrun + QLAT + FLF + WEL + GHB + DRN + RIV`.

`qmodf` is een interne koppelterm en wordt niet als extra externe flux bij `R0` opgeteld. `STO` en `BND` ontbreken in `R0`. Onderzoek `R0`, `R0+STO`, en `R0+STO+BND` als afzonderlijke diagnostische scenario's **alleen** bij brongetrouwe, werkelijk aanwezige termen met dezelfde cel- en tijdondersteuning. Geen STO-regime kiezen op basis van het kleinste residu; geen ontbrekende termen op nul zetten.

MODFLOW-termen zijn volledige celvolumes voor 62.500 m2; herhaalde celtermen per gekoppelde SVAT mogen nooit tot landelijke volumes worden gesommeerd. MetaSWAP-SVAT-volumes moeten via expliciete `area_svat.inp` en `mod2svat.inp` ondersteuning naar unieke cellen worden gebracht. De regel `qdr=0` voor deze toepassing en de bijzondere mogelijke laag-1 `qspgw`-bijdrage bij SVAT 207543 blijven behouden (bronbesluit 2 november 2026), maar worden niet zonder geverifieerd bronvolume gecorrigeerd.

De V04-velden `MSW_7term_afwijking_mm_j` en `Overall_onverklaard_volume_m3_per_j_cel` zijn **alleen beschrijvend**. Hun gemiddelden zijn geen fysieke sluitingsresultaten. Volledige STO/BND- en koppelboekhouding blijft open. `production_enabled=false` blijft staan.

## Uitvoering/controles

Lokaal pakket `LWKM_Frank_v04_Acceptatie_Waterbalans.zip` bevat een fail-closed ontvangstchecker, optionele controle van de nieuwe CSV-bytes op de NHI-server, een getrapte cel-dag-budgetvalidator en 13 geslaagde synthetische/receipttests. De scripts zelf zijn in dit document vastgelegd als downloadartefact en zijn **niet** in deze Git-commit geïmporteerd. Een serverbalansrun is niet uitgevoerd. De bronproducten hoeven niet opnieuw te worden berekend.

Vervolg: gekwalificeerde dagelijks getekende ruwe budgettermen op unieke laag-1 MODFLOW-cellen samenbrengen, ruimtelijke koppeling en bronregimes aantonen, dan pas fysieke sluitingscriteria beoordelen.
