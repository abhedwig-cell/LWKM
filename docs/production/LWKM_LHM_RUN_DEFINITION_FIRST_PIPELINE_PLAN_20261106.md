# LWKM productieketen vanaf de LHM-rundefinitie
Datum: 6 november 2026
Status: vastgesteld voorstel voor de volgende consolidatiefase, geen claim van bewezen LHM-runidentiteit.

## Aanleiding en afbakening
De ongecorrigeerde Frank SVAT 1991–2020-tabel is geproduceerd (645582 rijen). SHA256 uit de ontvangen productie-manifest: `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`. De losse producentpakketten en handmatige uitvoervolgorde zijn onvoldoende duurzaam.

Doel: **geen verandering van de wetenschappelijke rekenregels** tijdens reorganisatie. Eerst bewijsbare bronbinding, herhaalbaarheid, versiebeheer en eenduidige uitvoering. Lopende serverresultaten immutabel bewaren. QModF-uitzonderingen, SVAT-oppervlakten en MODFLOW-STO zijn eerder onderzocht, niet opnieuw tot nieuwe studieprojecten maken.

## 0. LHM-rundefinitie, vóór de LWKM-export
Maak één `lhm_run_definition.yaml` met:
- model: LHM 4.3.3; naam van de feitelijke run(s), status en verantwoordelijke bron;
- simulation_period(s), output_period, spinup, tijdstappen per component, restart_chain inclusief resume-input en begin/eindtijden;
- alle oorspronkelijke `control_run_*.ini` met SHA256 en periodebinding;
- model root `E:\LHM_4.3.3`, via daadwerkelijke INI-paden resolven;
- gebruikte MODFLOW modelconfig, packages, grids, laagindeling, tijdstap- en uitvoerselecties;
- MetaSWAP invoer zoals area_svat.inp, mod2svat.inp, meteorologie, landgebruik, bodem, beregening, uitvoerselecties en decade-contract;
- koppeling MODFLOW/MetaSWAP, fluxdefinities, tekens en ruimte/tijdsupport;
- correcties: originele FLF versus `diepe_slootkwel_gecorrigeerd` als **twee onafhankelijke bronreeksen**; originelen basis, correctievariant later;
- exacte authoritative result root `G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`, door Deltares samengesteld;
- known evidence gaps per veld (NOT_CONFIRMED, CONFIRMED_CONFIG, HASH_BOUND, SEMANTICALLY_QUALIFIED).

**Belangrijk:** een INI-verwijzing is geen bewijs dat de huidige bestanden byte-identiek zijn aan de historisch gebruikte. Evenmin bewijst de samenstelling van `LWKM_run_resultaten_totaal` uit welke `run_*` map ieder bestand fysiek kwam. Conform eerdere eigenaarbesluiten is een volledige reconstructie van Deltares' interne periodieke copy chain geen blocker voor gebruik van de aangewezen output authority, maar een **expliciete provenance-kwalificatie** wel nodig.

Bestaande basis: `config/source/w01-lhm-authority-v1.yml`, `docs/server/W01_LHM_AUTHORITY_SPLIT_2026-10-05.md`, `tools/server/lwkm_ini_provenance.ps1`, `config/source/w01-output-consumer-candidates-v1.yml`. Status in W01: `W01_OUTPUT_AUTHORITY_BOUND_INPUT_CONFIG_AUTHORITY_PARTIAL`. Begin bij deze provenancelaag, niet bij een losse nieuwe scan.

## 1. Bronregister (machineleesbaar)
Voor **ieder daadwerkelijk gelezen** invoerbestand: `logical_id, root, relpath, size, SHA256, period, units, temporal_support, spatial_support, sign, nodata, producer, consuming_step, authority_status`. Dagelijkse source families mogen compact via bestandsinventaris+horizon en bronhash-registratie. Voor louter statuscheck hoeven niet alle honderden GB opnieuw te worden gehasht; full qualification hashes zijn een aparte werkstap.

Geen bronzoektocht bij iedere productie. Source paths via runconfig; bronlijst is een gevalideerd contract.

## 2. Eén bronboom
`tools/lwkm_frank/`: `cli.py`, `config_schema.py`, `io/idf.py`, `io/area_svat.py`, `io/csv.py`, `sources/manifest.py`, `producers/metaswap.py`, `producers/modflow.py`, `producers/gxg.py`, `producers/et.py`, `producers/qmodf.py`, `producers/static.py`, `producers/gebied.py`, `assemblers/svat.py`, `validation/*.py`. **Eén** expliciete API voor source variables, geen nieuwe bestandspatronen per module. Alle scripts uit historische ZIP's eerst bytevast in Git opnemen en bij elke refactoring tegen de werkelijke output testen.

## 3. Eén aansturing en output-gates
Eén `RUN_LWKM_FRANK.cmd` vanuit de toolsmap:
```
RUN_LWKM_FRANK.cmd status
RUN_LWKM_FRANK.cmd verify
RUN_LWKM_FRANK.cmd run --profile svat-original
```
Outputs als immutable run-id directory, `run_manifest.json`, logs, QA gates. Een stap mag alleen hergebruikt worden wanneer input-/code-/config-fingerprints matchen; aanwezigheid van een CSV met 645582 rijen **alleen** volstaat niet. Atomair schrijven `.partial` -> final na validatie; locked concurrent runs; geen overschrijven van brondata.

Gecontroleerde transformatieketen:
```
LHM_INI_CONFIG + INPUT_IDENTITY + LHM_OUTPUT_AUTHORITY
   -> STATIC_SVAT + MSW_1991_2020 + MF_1991_2020 + GxG_14_28
   -> QMODF_HELPER + ET_COMPONENTS + GEOGRAPHY + GW_PERCENTILES
   -> SVAT_BASE_ORIGINAL
   -> (later) SVAT_FLEVO_BOOKKEEPING
   -> (later) SELECTION/DONOR REPLACEMENT
   -> (later) HRU DERIVATION
```
W01-config/output, W02–Wxx gescheiden; geen terugwaartse bronafleiding uit eindresultaten.

## 4. Referentie en regressie
Baseline: oorspronkelijke Frank-SVAT CSV SHA256 `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`, manifest `MANIFEST_FRANK_SVAT_BASIS.json`, audit `FRANK_SVAT_BASIS_CONTROLE_1991_2020.csv`. Vergelijk:
- byte-identieke CSV wanneer serializer onveranderd;
- anders per SVAT/per veld met expliciete numerieke tolerantie en nul onverklaarde verschillen;
- 645582 unieke SVATs, onveranderde oppervlakte, gebieds-NoData=88581, klassen, bronnen, tekenconventies, 16 fluxen, mm-j support, totale ET-controle en uitkomsten van beide **diagnostische** balansformules;
- QModF hoort bij hulpvariabele en niet dubbel in external overall; geen MODFLOW-storage, BND in deze referentie.
- Vlaar bekende uitzonderingen in een versioned `known_findings.yml` met bronverwijzing naar WB19–WB28, en maak geen onnodige nieuwe outlierstudies.

## 5. Definitie van gereed
A. Het LHM-configuratieregister is compleet of resterende gaps benoemd met materialiteitsbeoordeling.
B. Alle producentcode en lookups staan als bronbestanden in Git, niet alleen documentatiecommits.
C. Een clean installation op NHI draait zonder historische ZIP volgorde, handmatige kopieën of verborgen vaste paden.
D. Een volledig of gecontroleerd hergebruikte run produceert inhoudelijk dezelfde 1991–2020 SVAT-basis.
E. De Flevolandvariant ontstaat downstream uit bewezen originele basis en afzonderlijke gecorrigeerde FLF, nooit door stille vervanging.
F. Reproduceerbare releasebundel, gebruikershandleiding en machineleesbare runmanifesten.

## Eerstvolgende concrete actie
Het **run-definition dossier** maken op basis van alle reeds beschikbare LHM `control_run_*.ini`: gebruik bestaande `lwkm_ini_provenance.ps1`, leg per versie de relatie met input/static/forcing/outputs vast, en bind die aan het Frank bronregister. Dit kan read-only, zonder lopende productie te verstoren. Vervolgens bestaande geconsolideerde ZIP-broncode onder Git plaatsen, en instrumenteer de fingerprint-gates. Een losse bundel met één startbestand is niet voldoende om deze eisen te sluiten.
