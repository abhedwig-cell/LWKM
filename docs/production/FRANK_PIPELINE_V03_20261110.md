# LWKM Frank productieketen v0.3: broncodeherstel en proefherberekening

10 november 2026. Dit pakket vervangt geen historische Frank-resultaten.
Het sluit de nieuwe aansturing aan op de al uitgevoerde bronbinding.
De negen oorspronkelijke rekenmodules en drie readers zijn byte-identiek
behouden. Hun twaalf hashes worden tegen het bestaande register gecontroleerd.

## Wat je nu uitvoert

Pak de bovenste map LWKM_Frank_Pipeline_v03 uit de ZIP uit onder:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools

Open CMD in de map waarin CONTROLE_FRANK_V03.cmd staat:

```bat
CONTROLE_FRANK_V03.cmd
START_MSW_BASIS_V03.cmd
```

Voer START alleen uit wanneer CONTROLE met exitcode 0 is afgesloten.
De eerste opdracht controleert de run-lokale area_svat, de code en de 6480
vereiste MetaSWAP-IDFs voor de eerste module. De tweede rekent die module
opnieuw over 1991 tot en met 2020, in een afzonderlijke proefmap, en vergelijkt
aansluitend beide nieuwe CSV's met de oorspronkelijke MetaSWAP-export.
Geen van beide opdrachten start de overige acht producenten.

De bestaande bronbinding wordt gebruikt vanaf het pad dat jouw eerdere
commando daadwerkelijk heeft gerapporteerd:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_Frank_RunBinding_v01\run_source_binding.json

Deze binding hoef je niet opnieuw te maken of naar dit pakket te kopieren.
De volledige SHA256 van dat ontvangen bestand is vastgezet in de configuratie.
De input blijft run_1970_1979\metaswap\area_svat.inp. De selectie van deze
statische referentierun wijzigt de aggregatieperiode 1991 tot en met 2020 niet.

Python: E:\tools\deltaforge\deltaforge_4\python.exe, met NumPy.
Er wordt niets geinstalleerd. De CMD-bestanden controleren eerst de interpreter.

## Nieuwe uitvoer, strikt gescheiden

Alles wordt geschreven onder:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\Frank_v03_runlocal_1991_2020

De berekening gebruikt work\msw_basic voor onderhanden werk. Alleen na exitcode
0, een ongewijzigde bronregistratie en controle van de complete SVAT-populatie
wordt die map naar results\msw_basic verplaatst. Binnen die map staan:
- FRANK_LHM_SVAT_BASE_1991_2020.csv
- MSW_SOURCE_SIGNED_1991_2020.csv
- INPUTS_V03.json, COMMAND_V03.json, RECEIPT_V03.json en producer.log

Oorspronkelijke producentmanifesten behouden het pad van hun werkmap. Het
centrale receipt en de results-map zijn de publicatieplaats; dat padverschil
betekent niet dat uit de historische uitvoermappen is gelezen of geschreven.

PREFLIGHT_V03.json en STATUS_V03.json staan in de proefmap zelf. Na vergelijking
komt daar COMPARE_MSW_REFERENCE_V03.json bij. Dat is het eerste bestand om
terug te sturen. FIRST_STAGE_VALUES_EQUAL betekent gelijkheid van de twee
MetaSWAP-tabellen, niet kwalificatie van de volledige negenstapsketen.
Bij afwijkingen worden kolommen, aantallen en maximaal twintig voorbeelden
vastgelegd. Lege velden zijn niet gelijk aan nul. Numerieke vergelijking is
exact via Decimal, zonder tolerantie; alleen getalnotatie mag verschillen.
De volgorde en uniciteit van SVAT-ID's moeten gelijk zijn.

## Hervatten en stoppen

Opnieuw START uitvoeren hergebruikt een reeds afgeronde stap alleen wanneer
code, configuratie, bronregistratie en uitvoerhashes overeenkomen. Onderhanden
werk krijgt dezelfde identiteitstoets en gebruikt vervolgens uitsluitend de
bestaande checkpointregels van de oorspronkelijke producent. Onvolledige
jaarcheckpoints worden niet automatisch gerepareerd of gewist: de producent
kan dan stoppen en er is een nieuwe expliciete output_name nodig.

Een RUNNING.lock voorkomt twee gelijktijdige schrijvers naar dezelfde proefmap.
Verwijder die na een harde onderbreking uitsluitend nadat je hebt gecontroleerd
dat geen bijbehorend proces meer draait. Oude resultaten worden niet gewist.
Verander production_enabled niet; dat blijft false. diagnostic-run betekent
wel rekenen, maar niet het resultaat tot geaccepteerde productie verheffen.

## Controle van bronidentiteit

Code, configuratie, bronbinding, area_svat, relevante lookupbestanden en
tussenproducten hebben inhoudelijke SHA256-controles. De vele ruwe IDFs
gebruiken standaard pad, bestandsgrootte en wijzigingstijd. De SHA256 van die
registratie is GEEN inhoudelijke SHA256 per IDF. Deze begrenzing staat expliciet
in de receipts. De instelling source_hash_mode=sha256 biedt wel volledige
inhoudelijke hashing, maar leest alle ruwe bronbestanden aanvullend en verandert
de identiteit van de proefrun. Gebruik dan een nieuwe output_name.

Identieke statische invoer over de runs blijft een vastgesteld eigenaarbesluit.
Er wordt geen nieuwe vergelijking van alle run-invoermappen afgedwongen.
Broncodebesluit LWKM-LHM-SOURCE-20261110-01 wordt niet heropend.
De eerdere optionele infiltratie-ASC wordt alleen gebruikt als hij op het
bestaande expliciete workspace-pad aanwezig is; aanwezigheid of afwezigheid
wordt in de identiteit meegenomen. Die bestaande rekenregel is niet gewijzigd.

## Wat al is getest

71 unittest-tests slagen lokaal op Linux: de 24 bestaande bronbindingtests en
47 nieuwe tests. Daarnaast slagen de drie oorspronkelijke v0.2-testscripts.
De nieuwe aansturing is op een fixture met drie SVATs, 30 kalenderjaren en
6480 kleine IDFs daadwerkelijk uitgevoerd. Beide CSV's zijn byte-identiek aan
een afzonderlijke uitvoering van de oorspronkelijke module op dezelfde fixture.
Een NoData-geval blijft leeg, eenheidsfactoren en uitstroomtekens zijn getoetst,
en opnieuw starten gebruikt het afgeronde resultaat zonder producentaanroep.

Alleen de fixturelauncher vervangt in geheugen het vaste verwachte SVAT-aantal
door drie. Geen bronbestand of rekenformule is gewijzigd. De echte configuratie
blijft 645582 SVATs eisen. Tests zijn geen NHI-serverberekening en geen bewijs
van numerieke gelijkheid voor de overige acht modules. De Windows-CMD's zijn
in deze sessie niet op Windows uitgevoerd.

PLAN_FRANK_V03.cmd toont de aansturing van alle negen stappen zonder rekenen.
TEST_FRANK_V03.cmd voert de lokale fixturetests uit, zonder de echte NHI-data.
COMPARE_MSW_REFERENCE_V03.cmd herhaalt alleen de eerste-stapvergelijking.
De overige acht modules zijn aangesloten via expliciete argumenten, maar nog
niet met de echte run-lokale invoer doorgerekend of inhoudelijk vergeleken.

De oorspronkelijke eindtabel met SHA256
7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df
blijft beschermd. Deze eerste-stapvergelijking leest die eindtabel niet.
De twee lookup-CSV's en het ECHO-raster zitten exact uit v0.2 in dit serverpakket;
SOURCE_ASSETS.json legt hun hashes vast. Het grote ECHO-raster en de exacte
oude bodemlookup zijn in deze broncodecommit niet als Git-data opgenomen.
