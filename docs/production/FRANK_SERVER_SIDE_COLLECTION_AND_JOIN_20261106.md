# Frank: finale verwerking uitsluitend op NHI-server (6 november 2026)

Projecteigenaarbesluit: ontbrekende LHM/SVAT-gegevens rechtstreeks op NHI-server verzamelen, en **de grote samengestelde CSV op de server schrijven**, niet via ChatGPT upload of lokale samenvoeging. Python via `E:\tools\deltaforge\deltaforge_4\python.exe`.

## Uitvoerbaar pakket
`LWKM_Frank_Server_Samenstellen_v01.zip` beschikbaar als gebruikersdownload in deze conversatie. De pakketcode zelf is in deze release **nog niet als Git-sourceboom gecommit**; de bronbestanden zijn in de ZIP, met tests.

Onder `LWKM_tools\LWKM_Frank_Server_Samenstellen_v01`:
- `CONTROLE_EN_VERZAMEL.cmd`: read-only begrensde broninventaris (`BRONKANDIDATEN.csv`, `MAPCONTROLES.csv`) plus controles van veldconfiguratie; geen raster-auto-mapping op basis van naam alleen.
- `config_bronnen.json`: expliciete koppeling per classificatieveld aan geverifieerde LHM-gridbron. Standaard leeg voor velden waarvan de werkelijke bronlocatie niet aangetoond is.
- `VERZAMEL_GEGEVENS.cmd`: leest oorspronkelijke `area_svat.inp` (645582 IDs), geselecteerde IDF/ASCII-rasters, schrijft `FRANK_SVAT_EIGENSCHAPPEN.csv` en SHA256/dekking.
- `START_SAMENSTELLEN.cmd`: strikte SVAT join van `frank_export/FRANK_LHM_SVAT_BASE_1991_2020.csv`, `frank_export_heads/FRANK_LHM_SVAT_GXG_GG_1991_2020.csv`, `frank_export_modflow_bruto_v07/MF_SVAT_BRUTO_16_1991_2020.csv`, eventueel signed MSW diagnostiek en `FRANK_SVAT_EIGENSCHAPPEN.csv`. Stopt zolang v0.7 klimaatbestand ontbreekt; geen vermomde eindtabel met lege MODFLOW-waarden.

Uitvoer: `LWKM_run_resultaten_totaal/frank_export_eindtabel/samengesteld_v01/FRANK_SVAT_SAMENGESTELD_1991_2020.csv`, manifest (SHA256 bron-CSV's), velddekking. De 16 MODFLOW-brutofluxen blijven cumulatieve m3/volledige cel voor 1991–2020; aanvullende mm/jaar-cel-equivalenten zijn geen SVAT-gebiedsflux. Geen STO, BND, qmodf. RIV-systeem 1–4 kwel/infil gescheiden per tijdstap, DRN 1–3 alleen drainage, FLF kwel/wegzijging, netto QLAT/WEL/GHB.

**Toegelaten velden:** GG/GHG/GLG/GVG/dynamiek uit halfmaandelijkse heads; MetaSWAP neerslag, evapotranspiratie en oppervlakkige afstroming; extra 16 MODFLOW-brutofluxen. Totale rivierinfiltratie en ontwatering als **MODFLOW-cel-equivalente** mm/jaar, niet SVAT-oppervlaktegemiddelde. Bron gebonden classificaties/grondsoorten voorlopig alleen indien de originele geverifieerde rasterbron wordt aangewezen. Gebruikersbesluiten voor `Infiltratie`, `Fldrin345`, `GG`, `Dynamiek` behouden. Geen Fldrou1..5 vertaling uit 3 DRN/4 RIV zonder systemmapping. Geen vervangingsindicator of `N ???` verzinnen.

Dit maakt de **basis-SVAT-tabel**, niet de zeven conditionele LHM/LWKM-verwerkingsstappen. Die vergen afzonderlijk versioned selectie-/correctie-/replacement-input en HRU-representatiecontracten.

Lokale tests: synthetische ASCII-rasterproef met NoData, assembler SVAT-join op 16 fluxvelden, scripts compile, ZIP-integriteit. Echte NHI-run nog niet uitgevoerd. De mapinventaris moet eerst worden ontvangen om rasterpad- en betekenisbinding definitief te maken.
