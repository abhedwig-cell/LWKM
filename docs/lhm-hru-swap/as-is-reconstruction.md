# As-is reconstruction status

Status: **WORKING EVIDENCE MAP**
Date: 2026-09-24

Dit document beschrijft alleen voldoende van de huidige/historische LWKM 2.0 keten om de provenance van de actuele HRU10242-lijn te begrijpen. Het is geen poging om alle oude onderzoeksvarianten te documenteren.

## Scope

Wel:
- LHM/NHI export en nabewerking die downstream nodig is;
- SVAT-dataset en hydrologische selectie/correctie;
- actuele HRU10242-afleiding;
- HRU→SWAP-invoer;
- SWAP-QA en eindproduct voor overdracht.

Niet:
- volledige LHM-berekening;
- oudere HRU-indelingen behalve waar nodig voor provenance;
- downstream ANIMO-verwerking;
- vervallen onderzoeksvarianten zonder betekenis voor HRU10242.

## Huidige evidence

### LHM/NHI-zijde

Beschikbaar zijn batch/executable routes voor onder meer:

- MODFLOW-waterbalans;
- GVG/GxG-gerelateerde verwerking;
- klimaat/MetaSWAP-uitvoer;
- omzetting IDF→ASC;
- bundelen/overzetten van grote MODFLOW-uitvoer.

Het oude Protocol_LWKM beschrijft de historische fysieke overdracht LHM-server → laptop → Leo-server. Deze logistiek wordt niet als canonical doelarchitectuur overgenomen.

### Hydrologische rastervoorbewerking

Beschikbare gridcalc-batches produceren onder meer:

- neerslag;
- verdamping;
- runoff;
- kwel/wegzijging;
- drainage;
- infiltratie;
- beregening;
- bergingsverandering;
- selectie-/kwalificatierasters.

Een deel van de batches bevat zowel oude onderzoeksregels als latere afspraken. Aanwezigheid in een batchbestand is daarom niet automatisch bewijs dat een regel in de actuele productierun actief was.

### SVAT-dataset

LWKM_makeHRU is een centrale kandidaat-authority voor het samenbrengen van rasterinformatie tot een SVAT-tabel.

De beschikbare code bevat onder meer:
- domeinflag islwkm;
- hydrologische fluxen en toestanden;
- bodem- en landgebruiksklassen;
- afzonderlijke selectieflags;
- samengestelde verdachtheidsinformatie;
- aanvullende velden voor bron/vergelijking.

De exacte productiecontrol en de koppeling naar de definitieve current CSV moeten als provenance-evidence worden bewaard.

### SVAT-kwalificatie

De huidige lijn bevat regels voor hydrologisch verdachte situaties, onder andere rond kwel/wegzijging, runoff, infiltratie en grondwatercondities.

De canonical reconstructie zal deze regels splitsen in:
- diagnose;
- gebieds-/landgebruiksexcepties;
- usage policy;
- eventuele replacement.

De huidige implementatie heeft deze concepten niet overal volledig gescheiden.

### HRU10242

HRU10242 is de enige HRU-versie die in deze documentatielijn inhoudelijk centraal staat.

Beschikbare evidence omvat:
- technische documentatie van HRU_clustering_LWKM20_31082026.R;
- SVAT→HRU/NRU-koppeltabel;
- HRU-schema;
- NRU-schema;
- HRU-raster;
- representatieve-SVAT-informatie;
- controls voor HRU→SWAP.

De HRU-documentatie beschrijft hiërarchische clustering, clustering op GHG en NettoKwel, donor-matching en representatieve SVAT-selectie.

De feitelijke R-bron moet nog als canonical source worden toegevoegd en tegen de documentatie worden gereconcilieerd.

### HRU→SWAP

Beschikbare Fortran-bron en controls tonen een concrete HRU→SWAP-invoergenerator.

Belangrijk voor de canonical specificatie is dat verschillende SWAP-invoeronderdelen mogelijk verschillende representatie- en aggregatieregels gebruiken. Deze regels moeten uit de implementatie worden gehaald en expliciet in SWAP_MAPPING worden vastgelegd.

## Open evidence met hoogste prioriteit

1. Production source van HRU_clustering_LWKM20_31082026.R.
2. Exacte production control(s) die de actuele SVAT-table hebben geproduceerd.
3. Expliciete authority voor de Flevoland-correctie.
4. Exacte relatie tussen diagnoseflags en daadwerkelijke replacement/usage policies.
5. Volledige mappingtabel HRU/SVAT → ieder relevant SWAP-invoerveld.
6. QA- en vergelijkingsscripts die de actuele SWAP-resultaten beoordelen.

## Gebruik van historische documentatie

Eerdere markdown-, Word-, Visio- en batchdocumentatie is evidence en context. Zij wordt niet automatisch canonical.

Per onderdeel geldt:

RECONSTRUCT → CHECK AGAINST SOURCE → KEEP WHAT IS ACTIVE → DROP OBSOLETE VARIANTS → PERSIST CANONICAL SPECIFICATION

Daarmee voorkomen we dat jaren aan onderzoeksvarianten de toekomstige productieworkflow blijven vervuilen.
