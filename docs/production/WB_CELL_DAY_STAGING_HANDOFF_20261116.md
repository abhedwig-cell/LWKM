# LWKM WB cel/dag-staging v0.1, 16 november 2026

## Doel
Nieuwe afzonderlijke diagnostische cel-dagbalans: originele getekende MetaSWAP-termen op SVAT-steun via geautoriseerde area_svat + mod2svat omrekenen naar **m3 per dag per unieke MODFLOW-cel**, daarna MF-termen (op 62500 m2-celsteun) slechts eenmaal per cel meenemen. Qmodf is interne flux en wordt nooit als extra externe R0-term toegevoegd.

Dit sluit aan op de geverifieerde gecorrigeerde SVAT-kandidaat in PR #26 en op WB23, WB27, WB28 en het besluit WATERBALANS_QSAT_QMODF_BESLUIT_20261102.md. WB27/28 sluiten een automatische STO-keuze af; de omvang van de 5117 bekende niet-sluitende SVATs blijft in de afzonderlijke balansdiagnostiek zichtbaar en blokkeert niet bij voorbaat HRU-vervolgwerk.

## Werkelijk geleverd
Lokaal distributiepakket: `LWKM_WB_CellDay_v01.zip`; ZIP SHA256 `595000d2c0aae087a57a5e41146640179c9688088ec3bd8ec3cb9c0e16f477b8`. Python 3.8+ standaardbibliotheek en twee Windows CMD starters, 19 lokale unittest-tests geslaagd.

- `INVENTARISEER_WB_BRONNEN.cmd`: read-only inventaris van rolbenoemde MetaSWAP/MODFLOW-bronmappen voor 2020. Uitvoer `LWKM_tools/LWKM_WB_Broninventaris_2020.json`. Dit leest alleen bestandsnamen; geen bronidentiteit of dagdekking is hiermee geaccepteerd.
- `build_cell_day.py` en `START_WB_CELL_DAY.cmd`: één dag uit **expliciet geautoriseerde** CSV-exports. Vereist originele 645582-SVAT of voldoende gekwalificeerde lidmaatschapscontext, exacte hashes van area_svat/mod2svat/source binding, datum, ruimte- en tekensemantiek; faalt bij inconsistenties. Uitvoer `cell_day_staging.csv` + ontvangstbewijs.
- Bestaande `cell_budget_audit.py` leest één unieke MODFLOW-cel/dag zonder overschrijven en berekent gescheiden R0, R0+STO en R0+STO+BND, indien alle benodigde brontermen werkelijk beschikbaar zijn.

## Geen productie- of sluitingsclaim
**Er is geen originele server-IDF gelezen en er zijn geen werkelijke dagbalansen berekend in deze sessie.** De inputexports voor de stager zijn nog niet beschikbaar. Een YYYYMMDD-bestandsnaam kan een decade-einddatum vertegenwoordigen; dagdekking moet uit de bronproducer blijken. De juridische/canonieke modelbronautoriteit van 10 november en de gecorrigeerde maaiveldbron worden niet heropend.

De software uit het downloadpakket is in deze commit **niet als nieuwe bronbestanden in Git ingecheckt**; deze Git-wijziging is een overdrachts- en statusnotitie. De ZIP is leidend voor de exact geteste lokale tools. In dit stadium dus geen productievrijgave en geen merge van PR #26.
