# DRA rechtstreeks uit bestaande NHI-bronnen

Pak `LWKM_WorkE_DRA_Server01.zip` uit onder de gebruikelijke `LWKM_tools`-map.
Open CMD in de uitgepakte map met `maak_dra.cmd` en voer uit:

```cmd
maak_dra.cmd
```

De standaardperiode is 1970-01-01 tot en met 2022-12-31. Python wordt gestart
via `E:\tools\deltaforge\deltaforge_4\python.exe`. De starter toont de Python-
en NumPy-versie; pandas, XLS, SQLite en installatie van packages zijn niet nodig.
Er hoeven geen paden te worden veranderd. De SWP-procedure hoeft niet klaar te
zijn om DRA af te leiden. Controleer vóór SWAP de daadwerkelijk geschreven
SWP/DRA-bodemhorizonten en COFANI-lengte. Dit pakket bevat dezelfde HRU-CSV, membership en onafhankelijke bodemcatalogus.
Het wijzigt geen SWP-bestanden of reeds bestaande C2-resultaten.

Een kortere eerste serverproef voor alle HRU's kan met:

```cmd
maak_dra.cmd --start 1971-01-01 --end 1971-12-31 --output dra_proef_1971
```

Deel na afloop `dra_server_productie\controle.zip`, of bij de korte proef
`dra_proef_1971\controle.zip`. Ook bij een fout wordt een terugrapport geschreven.

## Bronnen en afleiding

De bronpaden en SHA-256-identiteiten komen rechtstreeks uit de eerder ontvangen
H1/MVG- en overige-drainage-Q4-registers. Ze staan in
`config/dra/server_sources_20261030.json`. De bestaande bestanden onder
`E:\LHM_4.3.3\Data\2_Model_Input` worden ter plaatse gelezen; er is geen nieuwe
BasicData-map of kopie van de modelinvoer nodig. Bronwijzigingen stoppen de
uitvoering en moeten eerst tegen de actuele runconfiguratie worden beoordeeld.

- Zeven fysieke systemen: H1, primair, secundair, tertiair, MVG, buisdrainage en OLF.
- Koppeling op de exacte SVAT-celcentra; geen interpolatie of rasterverschuiving.
- Positieve dqsat-mediaan van alle HRU-leden volgens het besluit van 2026-10-09,
  dezelfde implementatie en hetzelfde geïdentificeerde raster als SWP Server03.
  De bestaande serverlocaties worden automatisch doorzocht. Ontbreekt dit
  raster, dan vermeldt `dqsat_source_manifest.json` de onderzochte locaties.
- All-member drainage: de bestaande formule gebruikt 62.500 m² per lidcel en
  geleidingsgewogen bodemdiepten/peilen. `area_svat.inp` blijft de afzonderlijke
  oppervlaktebron voor MetaSWAP-aggregatie. Er wordt hier geen nieuwe
  donor-only-selectie ingevoerd. Het historische `nusvatwb` werd daadwerkelijk
  overschreven door `nusvat`; die broncode-observatie bewijst geen gewenste
  wetenschappelijke wijziging naar alleen waterbalansleden.
- P/S/T: bestaande zomer-/winterbodemgemiddelde; ontbrekend seizoenspeil mag
  volgens de bestaande eigenaarregel uit de bijbehorende bodem komen. Een
  daarna onvolledig RIV-record wordt met conductantie en SVAT-ID geregistreerd
  en uitgesloten. Een ontbrekende infiltratiefactor betekent nul infiltratie
  voor die cel, met behoud van drainage.
- H1: de werkelijke maandbestanden voor de aangevraagde periode. Voor volledige
  productie zijn dit 637 peilmomenten van 1970-01-01 tot en met 2023-01-01.
  Het laatste moment begrenst interpolatie tot de laatste simulatiedag, het
  verlengt de simulatie niet. Er wordt geen C2-jaarcyclus herhaald. Een gat bij
  een actieve H1-cel wordt als invoerfout geregistreerd, niet met nul opgevuld.
- Eigenaarbeleid vóór compressie: fysieke DRARES >100000 vervalt; bij INFRES
  >100000 vervalt alleen infiltratie. Exact 100000 geeft op zichzelf geen ingreep.
- Eerst bestaande beschermde compressie. Waar die geen vijf niveaus oplevert,
  volgt automatisch de bestaande best-fit-route volgens het definitieve
  eigenaarbesluit van 2026-10-21. Buisdrainage blijft apart. De status wordt dan
  `AUTO_APPROXIMATED_FIVE_LEVEL`, met fouten en bron-naar-niveau-toewijzing.
- COFANI-lengte volgt het aantal hydraulische bodemhorizonten uit dezelfde
  onafhankelijke catalogus als de SWP-generator, niet het aantal nieuwe rekenknopen.

## Uitvoer en hervatten

Uitvoer staat standaard onder `dra_server_productie`:

- `dra\<HRU>.dra`: werkelijk geserialiseerde DRA-invoer;
- `hrus\<HRU>.json.gz`: oorspronkelijke en behouden fysieke systemen, dqsat,
  eigenaaringrepen, gekozen niveaus, eventuele benaderingsfouten en uitvoerhash;
- `cell_decisions.json`: bronbesluiten per SVAT, inclusief uitgesloten conductantie;
- `source_manifest.json` en `dqsat_source_manifest.json`: bronpaden, hashes en beleid;
- `production_manifest.json`: resultaten en fouten per HRU;
- `controle.zip`: samenvatting en de volledige checkpoints van benaderde/foute HRU's;
- `cache`: gecontroleerde statische voorbereiding en afzonderlijke H1-maandcheckpoints.

Herhaal dezelfde opdracht na onderbreking. Reeds voorbereide maanden en
ongewijzigde HRU-bestanden worden hergebruikt. Bronbestanden worden opnieuw
gehasht; die controle kan enkele minuten duren. Invoer-, code- en periodehashes
voorkomen hergebruik van een voorbereiding van een andere configuratie.
Een mislukt HRU-bestand blijft niet als oude succesvolle uitvoer staan.

Voor een apart consolelog kan CMD-uitvoer worden omgeleid:

```cmd
maak_dra.cmd > dra_productie.log 2>&1
```

Dat verbergt de voortgang in het venster; zonder omleiding blijft die zichtbaar.

## Kwalificatiegrens

Werkelijke DRA-bytes en een complete tijdas zijn technisch bewijs. Het pakket
voert SWAP niet uit en verleent geen hydrologische productievrijgave. Een
benaderingsfout in mm/d is een responsdiagnose over voorgeschreven grondwater-
diepten. Het trapeziumgewogen cumulatieve verschil hoort bij hypothetische
constante-dieptescenario's, niet bij een gesimuleerde historische waterbalans.
De nieuwe bestanden moeten nog samen met BBC/MET/CRP/SWP worden doorgerekend.
