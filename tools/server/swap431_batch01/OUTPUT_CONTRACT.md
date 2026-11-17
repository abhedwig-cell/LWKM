# Gebonden dagelijkse uitvoer: SWAP 4.3.1 / Server06

## Werkelijke bronbasis

De zes ontvangen `MET_HUM_PROEF_TERUG.zip`-gevallen gebruiken `SWCSV=1`,
`NPRINTDAY=1`, `PERIOD=1`, `SWMONTH=0`. Hun native CSV-header noemt modelversie
4.3.1 en cm voor alle twintig numerieke kolommen. De volledige CSV staat op de
server. De meegeleverde testfixtures bevatten uitsluitend oorspronkelijke
een kop/staartfragment en gerichte, letterlijk overgenomen invoerregels, geen volledige modeluitvoer.
`SOURCE_EXTRACTS.json` binnen de fixture-JSON bewaart originele en extracthashes.
Deze extracten zijn alleen parsertests, geen uitvoerbare modelcases.

De betekenis van de fluxvelden is gecontroleerd in de oorspronkelijke regels
van `SWAP_4.3.1/swap_csv_output.f90`, `set_values_scalar`, zichtbaar als oude
regels in het aangeleverde `S11_cumulative_from_pristine.patch`, vanaf originele
bronregels 447 en 465. De nieuwe S11-code wordt niet uitgevoerd of als executable
voor deze campagne gebruikt. Deze patch is een inspectiebron voor de oorspronkelijke
toewijzingen, niet een nieuwe waterbalansreconstructie.

| Native kolom | Oorspronkelijke toewijzing | Aggregatie |
|---|---|---|
| RAIN | igrai + isnrai | Som van dagelijkse uitvoerintervallen |
| IRRIG / RUNOFF | igird / iruno | Som |
| EIC / EPD | iintc / iepd | Som, componenten afzonderlijk |
| EPOT / EACT | ipeva / ievap | Som, geen claim totale verdamping |
| TPOT / TACT | iptra / iqrot | Som |
| TREDDRY / TREDWET | iqreddry / iqredwet | Som |
| DRN | iqdra + iQMpOutDrRap | Som met oorspronkelijk teken |
| SSDI | iqssdi | Som met oorspronkelijk teken |
| BOT | -iqbdo + iqbup | Som met oorspronkelijk teken |
| DSTOR | totale berging minus beginberging van uitvoerinterval | Som van veranderingen |
| GWL / PD_VOL / IC_VOL / WTOT | Native toestandskolommen | Gemiddelde, minimum, maximum en eindwaarde |
| BALDEV | Native door SWAP berekende balansafwijking | Som, absolute som, maximum absoluut, RMS |

Er wordt geen nieuw balansresidu uit geselecteerde CSV-kolommen gereconstrueerd.
Geen numerieke BALDEV-tolerantie wordt als vastgesteld projectbesluit ingevuld.
Technische acceptatie vereist een complete eindige reeks en normale procesafsluiting.
De BALDEV-statistiek is afzonderlijke diagnostiek, geen automatische hydrologische
of wetenschappelijke vrijgave.

De controle weigert een andere header, ontbrekende expliciete cm-eenheden,
andere modelversie of een afwijkende dagelijkse uitvoerinstelling. Voor andere
uitvoerprofielen is een expliciete nieuwe contractversie nodig; geen gokken op
basis van een kolomnaam.

## Kalender en vergelijkbaarheid

De beginrij van 31 december 1969 wordt op tijdas en eindige waarden getoetst maar
niet bij de 19.358 simulatie-etmalen opgeteld. De eerste echte dag is 1 januari
1970, de laatste 31 december 2022. Jaar- en decadetabellen omvatten de volledige
berekende periode. Decaden zijn kalenderdagen 1 t/m 10, 11 t/m 20 en 21 t/m
maandeinde. Schrikkeldagen tellen gewoon mee.

Er is nog geen inhoudelijke vergelijkingsperiode of spin-up-uitsluiting gekozen:
`comparison_period=null`, `spinup_exclusion_applied=false`. GxG en de vergelijking
met LHM moeten later aan de bestaande projectdefinities en run-lokale
`area_svat.inp`-maaiveldreferentie worden gebonden. Dit pakket verandert die niet.
