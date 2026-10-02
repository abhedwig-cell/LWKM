# LWKM projectstatus voor overleg — 2026-10-02

## Kernboodschap

De reconstructie van de LHM -> SVAT -> HRU -> SWAP-productielijn is inhoudelijk ver gevorderd. De hoofdstructuur, het huidige datamodel, een historische 49-run oracle, belangrijke DRA-semantiek en de Python-postprocessing zijn teruggevonden of opgebouwd.

De resterende onzekerheid zit niet meer vooral in "hoe werkt de keten?", maar in "welke exacte historische versie en inputs hebben deze specifieke oude outputs gemaakt?" en in de laatste server/end-to-end kwalificatie.

Daarom moeten we twee doelen uit elkaar houden:

1. historische reproduceerbaarheid van de oude productierun;
2. een moderne, deterministische en onderhoudbare productielijn.

Die doelen overlappen, maar historische defecten of onbekende builddetails mogen niet automatisch moderne production authority worden.

## Wat we nu zeker weten

### 1. Huidig datamodel is bruikbaar

`Datamodel_10242.xlsx` is hersteld en direct uitleesbaar.

Resultaat:
- 22 worksheets;
- 10.242 Runs;
- alle 10.242 typed contexts resolve;
- geen unresolved required joins;
- 337.098 formulecellen bevatten opgeslagen waarden.

We zijn dus niet afhankelijk van een oude SQLite-versie om verder te kunnen.

### 2. Historische testset is terug

De 49 historische realized runs zijn beschikbaar met:
- SWP;
- DRA;
- BBC;
- MET.

Hiermee kunnen we echte historische output vergelijken in plaats van alleen uit broncode te redeneren.

### 3. Een belangrijk DRA-verschil is verklaard

Voor drainage spacing gebruikt de historische 49-run executable in 15 discriminerende gevallen de oude majority-BFE dqsat.

De moderne route gebruikt bewust representative-SVAT dqsat.

Daarom zijn 75 verschillen in `L` vooraf als intentioneel vastgelegd. Dat is dus geen open bug meer.

### 4. SWALLO is grotendeels gereconstrueerd

De huidige v0.38-regel verklaart 241 van 245 historische waarden.

Vier oude waarden, verdeeld over HRU 7868 en 7929, blijven provenancevragen.

Een generieke regel "systemen 3-5 altijd SWALLO=3" is aantoonbaar fout voor deze 49 runs.

### 5. De oude DRA-bron bevat een echt programmeerdefect

De meegeleverde `AVERAGE`-routine leest bij N>1 de functiewaarde vóór initialisatie.

Dat is een echt source defect.

Maar we weten niet of precies die routine/binair in de historische run zat of welk runtimegedrag de compiler gaf. We gaan dit dus niet nabootsen in de moderne Python-code.

### 6. Historische producer is nu beter gebonden

De operationele batch roept aan:

```bat
exe\HRU2SWAP.exe HRUSWAP_test.log control_LHM433_HRU_SWAP_10242.inp
```

Daarmee weten we welke executable- en lognaam de productieroute verwachtte.

De binary zelf en de historische log zijn nog niet teruggevonden.

### 7. Chronologie wijst waarschijnlijk naar pre-v0.38

De 49 DRA-files hebben ZIP-membertijd 24 maart 2026.

De bronhistorie noemt:
- v0.35 en v0.36 in maart;
- v0.37 en v0.38 in april;
- v0.38 specifiek als drainageweerstandsbugfix voor geselecteerde cellen.

Dat maakt een pre-v0.38 selected-member versie een serieuze hypothese.

Het is nog geen bewijs van v0.35 of v0.36.

### 8. Python server-postprocessing staat inhoudelijk

De nieuwe Python-kern kan de eenvoudige oude batch/Fortran-postprocessing vervangen voor:
- IDF-aggregaties;
- MODFLOW volume -> mm;
- positieve/negatieve fluxsplitsing;
- toestandsgemiddelden;
- eenvoudige rasteralgebra;
- strikte geometry/NODATA-validatie.

Wat nog ontbreekt is een golden regression op een echte kleine LHM-serverperiode.

## Wat nog niet rond is

### SWP

De exacte oude `swap_wwl.swp`-template ontbreekt.

De huidige `wwl.swp` is aantoonbaar een andere versie en past niet stil in de oude adapter.

Daarom is de directe SWP-renderer nog niet admitted.

### DRA

De actuele recovered rasters reproduceren de historische DRA-waarden niet breed genoeg:
- 226/245 DRARES verschillen;
- 133/245 INFRES verschillen;
- 230/245 ZBOTDR verschillen;
- 230/245 seasonal LEVEL-systemen verschillen.

Dit betekent vooral dat historische input/source/build provenance nog niet gebonden is. Het betekent niet automatisch dat de moderne all-member rekenwijze fout is.

### Ontbrekende historische artefacten

De belangrijkste nog gezochte bestanden zijn:
- March-2026 `HRU2SWAP.exe`;
- `HRUSWAP_test.log`;
- v0.35/v0.36 source/project snapshot;
- historische `verdacht.asc`;
- `lengte_p_250.asc`;
- `lengte_s_250.asc`;
- `lengte_t_250.asc`;
- exacte historische `swap_wwl.swp`.

### Serverkwalificatie

Nog nodig:
- een kleine historische LHM-serverperiode plus de bijbehorende oude outputs;
- golden regression oude route versus Python;
- daarna pas volledige servermigratie;
- real-source Q4 bundle;
- uiteindelijk 10.242-run end-to-end test.

## Wat ik in het overleg zou willen uitzoeken

De meeste winst zit nu niet in opnieuw programmeren, maar in weten of collega/projectopslag nog historische runtime-evidence heeft.

Concrete vragen:

1. Staat of stond `exe\HRU2SWAP.exe` nog op de LHM-server of in een oude werkmap/back-up?
2. Is `HRUSWAP_test.log` van de run rond maart 2026 nog ergens aanwezig?
3. Zijn er v0.35 of v0.36 snapshots van `HRUlist2SWAP.f90`, bijvoorbeeld in een oude Visual Studio-projectmap of back-up?
4. Waar kwam `verdacht.asc` exact vandaan voor die productierun?
5. Zijn `lengte_p_250.asc`, `lengte_s_250.asc` en `lengte_t_250.asc` nog beschikbaar?
6. Is de oude `swap_wwl.swp` nog terug te vinden in een template-, WWL- of Martin-map?
7. Welke oude batch/Fortran-postprocessingproducten zijn operationeel nog echt nodig?
8. Kunnen we één kleine complete serverperiode aanwijzen voor golden regression?

## Voorstel voor vervolg

### Korte termijn

- historische producer/template/mask/length-files terugvinden en hashen;
- één kleine real-server golden regression uitvoeren;
- indien pre-v0.38 source/mask gevonden wordt: selected-member DRA-hypothese tegen alle 49 runs testen.

### Daarna

- 49-run DRA-gate sluiten;
- 49-run SWP-gate sluiten;
- Q4 source bundle kwalificeren;
- declaratieve Python-orchestratie afronden;
- volledige 10.242-run productie-smoke en admission.

## Status in één zin

We hebben de keten grotendeels gereconstrueerd en de moderne richting is duidelijk; de resterende technische onzekerheid zit vooral in ontbrekende historische runtime-evidence en de laatste server/end-to-end regressies, niet meer in het fundamentele ontwerp van de nieuwe productielijn.
