# WB28: STO uit grondwaterstandsverandering, januari 2020

**Besluit projecteigenaar 4 november 2026:** onderzoek afsluiten en terug naar productie; geen empirische STO-factor of per-cel bergingsregime in de HRU-keten opnemen.

De originele NHI-run leverde `uitvoer_WB28.zip`, status `COMPLETED_DIAGNOSTIC_NOT_PRODUCTION_AUTHORITY`, 645574 SVATs, begin/eindstijghoogten 2019-12-31 tot 2020-01-31 met tussendata 2020-01-10 en 2020-01-20. Getoetst `STO=-62500*0.2*delta_h` bij de originele MODFLOW-STO-volumes en MODFLOW-tekencontract; ratio alleen `abs(delta_h)>=0.02m`.

Klasse 2, 47029 SVATs, 37702 met voldoende delta_h: mediaan `S_eff = 0.1538441`, 10/90-percentiel `0.0662429/0.2717844`, 31.81% binnen 10% van 0.20, 34.00% binnen 20%, MAE van vaste 0.20: 196.83 m3/cel/maand. Gewogen fit `0.1329968`. Een vaste coëfficiënt 0.20 reproduceert de oorspronkelijke STO niet voldoende. Tijdintegratie en koppeldynamiek blijven mogelijk relevant.

Deze uitkomst **rechtvaardigt geen** aanpassing van de hydrologische fluxen. De door gebruiker aangeleverde Fortran-code `msw1postfm.for` bevat een variabele koppeling-`sc1`, maar het precieze verband met het feitelijke MODFLOW-STO is niet uit deze diagnose afgeleid.

Geen vervolganalyse WB28 gepland.