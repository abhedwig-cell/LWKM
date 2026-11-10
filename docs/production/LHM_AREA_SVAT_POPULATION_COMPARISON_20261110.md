# LHM area_svat versus svat_border, SVAT-populatievergelijking v0.1

Datum 10 november 2026. Gebruiker heeft de gerichte vergelijking aangevraagd na NHI SHA-proef met 0 byte-identieke paren, 8 verschillende paren en 2 eenzijdig ontbrekende bestanden.

## Nieuwe serverprocedure
In de gebruikersconversatie geleverd als `LWKM_LHM_SVAT_Populatievergelijking_v01.zip`, met Python-script, CMD-starter, LEESMIJ en vier lokale regressietests. **De Python-broncode zit in de ZIP en is op dit moment nog niet als Git-bronbestand geïntegreerd.** Lokale regressietest: 4/4 PASS. ZIP-integriteit PASS; geen NHI-serveruitvoering geclaimd.

Start vanuit uitgepakte map onder `LWKM_tools` met `START_SVAT_POPULATIEVERGELIJKING.cmd`. Python `E:\tools\deltaforge\deltaforge_4\python.exe`. De procedure vergelijkt uitsluitend:
- `E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp`
- `E:\LHM_4.3.3\Data\2_Model_Input\metaswap\svat_border\area_svat.inp`

Read-only SQLite-vergelijking over SVAT-ID: beide aantallen, unieke ID's, doorsnede, ontbrekende ID's per kant en per gedeelde ID verschillen in `ark,glk,tempCbotk,slk,soil_description,luk,dprzk,nm,cfPm,cfETref`. Gebruikt de vaste kolommen uit de MetaSWAP-IO-handleiding; geen whitespace split voor de velden. Volledige CSV-lijsten uitsluitend voor ID's buiten de overlap; hoogstens 5000 attribuutverschillen in voorbeeldbestand. SHA256 van beide invoerbestanden geregistreerd. Fout bij dubbele ID, ongeldige vaste velden en ontbrekende bron. Oorspronkelijke gegevens niet gewijzigd.

Uitvoer onder `LWKM_tools/LWKM_LHM_RunDef_resultaten_v01/svat_population_compare`: `SVAT_POPULATIEVERGELIJKING.json`, `verschillen_per_veld.csv`, `verschillen_voorbeeld.csv`, `alleen_in_inp.csv`, `alleen_in_svat_border.csv`.

**Methodische beperking:** het officiële `area_svat.inp` bevat geen RD-X/Y in zijn eerste 98 vaste kolommen. De afzonderlijke X/Y-koppeling wordt niet geraden. Later apart binden via daadwerkelijk gebruikte SVAT-grid/geometry en originele INI. Uit een deelverzamelingsrelatie volgt evenmin de bewijsstatus van de historische run. Het projecteigenaarbesluit `LWKM-LHM-SOURCE-20261110-01` over de `IMODFLOW.ZIP`-broncode/executable wordt niet opnieuw geopend.

Volgende gate: het echte NHI-rapport beoordelen en de bewezen SVAT-identiteits- en attribuutrelatie vastleggen. Geen wijziging aan Frank-SVAT-basistabel SHA256 `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`.
