# MET07: landelijke HUM-correctie en W11-herbinding gereed voor serveruitvoering

17 november 2026. Opdracht projecteigenaar: voer de landelijke correctie en herbinding uit na de zes geslaagde volledige SWAP 4.3.1-proeven. Vanuit deze sessie is de NHI-server niet bereikbaar; daarom is het concrete serverpakket gebouwd en getest. Er wordt geen landelijke serveruitvoering geclaimd.

## Geleverde distributie

`LWKM_MET07_HUM_Landelijk_v01.zip`

- Omvang: 2163408 bytes.
- SHA256: `ae055c77d0ea64dc75e8a33413e2bf52b84c7f2b55442563a6b4b5ff3da722d8`.
- Nieuwe driver `national_hum.py`: 31512 bytes, SHA256 `359daf52362229d526f7538c5c377a24b96eafed038320846e0c6b45bb4d6a77`.
- Nieuwe tests `tests/test_national_hum.py`: 15087 bytes, SHA256 `db76b3c648bba35d406b1e4d0ef5a5344423333b86f616e47528bdca14a0227b`.
- PACKAGE_MANIFEST.json bindt alle 39 overige pakketbestanden. De CMD-starter controleert deze hashes voor de uitvoering.

Het distributiepakket bevat de volledige nieuwe broncode, tests, configuratie en benodigde ongewijzigde proef-/W11-modules. Deze Git-commit bevat de overdracht en exacte distributie-identiteit; hij importeert die nieuwe Python-bestanden niet als afzonderlijke repositorybronbestanden. Geen volledige repository-integratie of merge naar main geclaimd.

## Uitgangspunt en grenzen

De bestaande assemblage van alle 10242 HRU's blijft het uitgangspunt. Oude runmappen: `LWKM_rebuilds\SWAP_HRU_Server06_1970_2022_v01`. De nationale assemblagerapporten zijn ongewijzigd meegeleverd en hun hashes/populatie/onderlinge koppeling worden gecontroleerd.

De ontvangen `MET_HUM_PROEF_TERUG.zip`, SHA256 `d3051a4a326168e9cd6c098d901c051e557042a87323275038667a219872dac5`, is opnieuw rechtstreeks geopend. STATUS_MET_HUM_PROEF.json, RUN_RESULTS.json, HUM_CORRECTIONS.json en het volledige bronregister zitten ongewijzigd in de distributie. Hun onderlinge koppelingen worden door de nationale driver getoetst.

De nationale correctie gebruikt exact hetzelfde HUM-broncontract en dezelfde gewichten als het geslaagde proefpakket `LWKM_MET07_HUM_Herstel_Proef_v01.zip`, SHA256 `704b27457b370c329d164e62190637c3e6c52f932bb5785502280e58786739ae`. De kernel `tools/met_hum_repair.py` is ongewijzigd behouden. Geen nieuwe conversiefactor, vochtigheidsafleiding of FG-koppeling.

## Concrete verwerking

1. Gebruik uitsluitend oorspronkelijke LHM-UG-rasters: werkelijke dampdruk, kPa, schaal 1. Per datum moet de bronhash exact overeenkomen met het al ontvangen volledige UG-register van de zes geslaagde proeven, SHA256 `86ff1262f407bcc2287315fd2dd39eedcbdaeb5da3d31fd35d5c9059400683a5`.
2. Bind de geautoriseerde gewichten aan SHA256 `6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c`. Geen hernormalisatie of selectieve oppervlakte-uitval.
3. Verwerk alle HRU's gezamenlijk per jaar. De float64-optelvolgorde binnen iedere HRU blijft gelijk aan de proefkern. De vectorisatie loopt over HRU's, niet over een geherassocieerde som binnen een HRU. Bij NoData geldt dezelfde dichtstbijzijnde oorspronkelijke geldige pixel en laagste rij-volgorde-index bij gelijke afstand. Donors zijn alleen oorspronkelijke geldige pixels. Fysiek ongeldige vochtigheid wordt niet vervangen of afgekapt.
4. Schrijf gehashte jaarcaches en dagelijkse bron-/donorregisters. Reeds voltooide caches worden bij hervatten op inhoud, identiteit en kalender gecontroleerd, niet opnieuw numeriek afgeleid. Dit is hergebruik van een gebonden bronmomentopname, geen nieuwe inspectie van alle levende bronrasters.
5. Corrigeer eerst HRU 1, 3, 181, 7870, 7871 en 7929. De complete nieuwe MET-hash moet voor elk exact overeenkomen met de ontvangen proefhash. Bij een verschil stopt de procedure voordat de overige HRU's worden verwerkt.
6. Verander uitsluitend het HUM-token in nieuwe MET-derivaten. Alle overige tokens, witruimte, regeleinden en datums blijven bytegelijk. Een onafhankelijke tweede vergelijking controleert de werkelijk geschreven bestanden.
7. Maak met de bestaande Python-W11-assembler nieuwe broncatalogi en kandidaat-runmappen. SWP, DRA, BBC, CRP en CO2 blijven byte-identiek. De periode blijft 1970-01-01 tot en met 2022-12-31. Geen SWAP-aanroep en geen automatische productie-admission.

## Bronnen beschermen en hervatten

De oude MET06-uitvoer en oude kandidaat-runmappen worden niet gewijzigd of verwijderd. Alle nieuwe paden zijn expliciet gescheiden van de bronmappen. Nieuwe MET-derivaten en jaren worden via tijdelijke directories gepubliceerd. Bestaande afgeronde outputs worden alleen hergebruikt na controle; een gewijzigde bron, afgeleide, catalogus of runmap wordt geweigerd, niet overschreven.

OS-bestandslocks voorkomen gelijktijdig schrijven en worden automatisch vrijgegeven bij proceseinde. Een onderbroken onvoltooid jaar wordt opnieuw opgebouwd, voltooide jaren en HRU's worden gecontroleerd hergebruikt. Gewijzigde code of configuratie kan niet ongemerkt een bestaande binding voortzetten.

De eerste start gebruikt een conservatieve ruimtecontrole van 54890745222 bytes, circa 55 GB vrije ruimte bij deze populatie. Dit is een uitvoeringsbudget, geen gemeten uiteindelijke opslag. De numerieke jaarcache voor de hele periode omvat circa 1,59 GB. Er worden echte kopieen gebruikt, geen hardlinks. Geen automatische opschoning van oude bestanden.

## Startopdracht en locaties

ZIP uitpakken onder de bestaande LWKM_tools-map. Vanuit de directory waarin de starter staat:

```cmd
HERSTEL_HUM_LANDELIJK.cmd
```

Gebruikt de bestaande `E:\tools\deltaforge\deltaforge_4\python.exe`, Python 3.8+ met NumPy. Alle serverpaden zijn ingevuld. De extra uitpakdirectory is toegestaan.

Nieuwe kandidaat-runmappen:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\SWAP_HRU_Server06_MET07_1970_2022_v01
```

Correcte MET-derivaten en jaarcache:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\MET07_HUM_Landelijk_v01
```

Terugrapport:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_MET07_HUM_Landelijk_v01_resultaat\MET07_LANDELIJK_TERUG.zip
```

`OPEN_RESULTAAT.cmd` opent de rapportmap. De ZIP bevat status, alle HRU-resultaten, zes regressiehashcontroles, jaarcachegegevens, het nationale dagelijkse bron-/donorregister en bij een fout een traceback. De grote modelbestanden blijven op de server.

## Werkelijk geteste reikwijdte

86 unittest-tests geslaagd in de bouwmap en opnieuw vanuit de definitieve uitgepakte ZIP: 27 nieuwe landelijke tests en 59 behouden proefroute-tests. Alle Python-bestanden zijn met Python-3.8-grammatica geparsed. Het pakketmanifest is ook vanuit een andere werkdirectory gecontroleerd.

Nieuwe tests omvatten bitgelijke aggregatie tegenover de proefkern voor 10242 synthetische HRU's, de twee echte rasterreplays, volledige synthetische correctie/W11-herbinding, twee kalenderjaren, onderbreking tijdens een jaar en tijdens herbinding, hervatten, gewijzigd bronbestand, gecorrigeerde MET, nieuwe runmap en jaarcache, afwijzen van verkeerde regressiehashes, niet-HUM-bytegelijkheid, padoverlap en locks. De behouden modelprocesproeven gebruiken een synthetisch proces, niet de SWAP-executable.

Geen volledige landelijke lezing van de originele server-UG-reeks, nationale modelberekening of nationale productie-admission geclaimd. De zes volledige MET-hashregressies worden op de server uitgevoerd; de grote zes gecorrigeerde MET-bestanden zijn niet lokaal ontvangen. De Windows-CMD-starter en de Windows-locktak zijn niet op Windows getest in deze sessie.

Bij volledige geslaagde serveruitvoering is de verwachte status `ALL_10242_HUM_CORRECTED_REBOUND_NOT_PRODUCTION_ADMITTED`, completed=10242, failed=0, regression_anchors_matched=6, swap_executed=false. Dat is correctie en herbinding, geen wetenschappelijke vrijgave. Geen heropening van het LHM-waterbalansonderzoek of de afleiding van SWP/DRA/BBC.
