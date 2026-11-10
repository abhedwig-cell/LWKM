# LWKM: hervatting productieketen v0.2

Datum: 10 november 2026.
Herstelpunt: `e7a92db6b88ee56c62abaf94eff831178c3bfdaf` op
`work/wb07-qmodf-climate-20261103`.

## Wat v0.2 daadwerkelijk opleverde

De eerdere zoekslag op alleen main miste de oplevering. Het bijbehorende document
is `docs/production/FRANK_PIPELINE_V02_SOURCE_GATES_20261110.md`.
De status is LOKAAL GETEST, NHI-NIET-UITGEVOERD, GEEN NIEUWE PRODUCTIE TOEGELATEN.
Het pakket is `LWKM_Frank_Pipeline_v02_Bronbeheer.zip`.

Volgens de oplevering bevat dat pakket negen originele producenten en drie
readers, byte-identiek aan v0.1. De twaalf SHA256's staan al in
`config/production/frank_original_producers_sha256_v01.json`, maar de twaalf
bronbestanden zijn nog niet als losse bestanden onder `tools/lwkm_frank/legacy`
opgenomen. De controller staat nieuwe berekeningen bewust niet toe.
`START_FRANK.cmd` uit v0.2 is dus geen vrijgave voor nieuwe productie.

Het originele ZIP is in de Library teruggevonden, maar materialisatie van de
inhoud naar deze werkomgeving is mislukt: geen geautoriseerd raw-byte-pad.
Daarom zijn de oorspronkelijke rekenmodules hier niet opnieuw getest,
geimporteerd, gewijzigd of gereconstrueerd. Hun hashes zijn niet opnieuw tegen
het ZIP gecontroleerd. De onderstaande aanvulling bevat die modules niet.

## Uitgevoerde vervolgstap: expliciete bronbinding

Nieuwe bestanden:
- `tools/lwkm_frank/run_source_binding.py`
- `tools/lwkm_frank/BIND_RUN_SOURCES.cmd`
- `config/production/frank_run_source_binding_v01.json`
- `tests/test_lwkm_frank_run_source_binding.py`

De centrale configuratie wijst rechtstreeks naar:
`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\run_1970_1979\metaswap\area_svat.inp`.
Er wordt geen extra `inp`-submap verondersteld. Een andere relatieve locatie is
alleen toegestaan wanneer deze expliciet in de configuratie wordt gezet.
Geen `svat_border`, geen globale E:-terugval, geen recursieve padkeuze.

De overige vijf bestandsnamen zijn overgenomen uit de bestaande run-lokale
inventarisator: mod2svat, scap_svat, dldra_svat, dqsat_svat en idf_svat.
Ze worden hier, indien aanwezig op hun expliciete pad, geregistreerd en gehasht.
Ontbrekende optionele bestanden worden zichtbaar gerapporteerd. Dit is geen
verklaring dat de volledige invoerset voor alle producenten compleet is.
Producentgebonden verplichte bestanden moeten bij de integratie worden benoemd.

Het programma schrijft uitsluitend een nieuw bronmanifest in de afzonderlijke
map `LWKM_tools\LWKM_Frank_RunBinding_v01`. Het start geen producent, leest of
hergebruikt de historische Frank-tabel niet en schrijft niet in LHM-invoer of
`LWKM_run_resultaten_totaal`. Aanwezige inputbestanden, configuratie en eigen code
krijgen een SHA256. Bestaande bronbestanden worden niet gewijzigd.
Een mislukte validatie laat een eventueel eerder manifest staan; alleen een
uitvoering met exitcode 0 en de nieuwe uitvoertijd is een geslaagde nieuwe binding.

Het bestaande INI-inventarisbestand wordt, indien beschikbaar, als context
meegenomen. Varianten blijven afzonderlijk zichtbaar; er wordt niet automatisch
gekozen welke variant daadwerkelijk heeft gedraaid. Het ontbreken van deze
context blokkeert de beperkte bronbinding niet en geeft geen productievrijgave.

Behouden besluiten:
- Statische inputidentiteit tussen runs is door de eigenaar vastgesteld.
- Vergelijkende hashes tussen runs blijven optionele QA, geen terugkerende eis.
- Broncode/executable-authority `LWKM-LHM-SOURCE-20261110-01` wordt niet heropend.
- De geselecteerde statische referentierun 1970-1979 verandert de historische
  Frank-vergelijkingsperiode 1991-2020 niet.
- De oude referentie-SHA256 blijft
  `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`.

## Tests en begrenzing

24 lokale unittest-tests zijn geslaagd, inclusief werkelijke CLI-aanroepen op
synthetische fixtures, fout-exitcodes, expliciete padkeuze, padontsnapping,
behoud van bronbestanden, atomair schrijven en behoud van bestaand manifest bij
fouten. `py_compile` is geslaagd. De tests zijn uitgevoerd op Linux; de Windows
CMD-starters en echte NHI-bestanden zijn in deze sessie niet uitgevoerd.
Dit is geen numerieke regressie, geen controle van 645582 SVATs en geen
kwalificatie van de volledige productieketen. Het manifest vermeldt expliciet
`SOURCE_BINDING_ONLY` en `production_enabled=false`.

## Uitvoering van alleen deze aanvulling

Gebruik het pakket `LWKM_Frank_RunBinding_v01.zip`. Pak de bovenste map uit onder
`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools`.
Open CMD in de uitgepakte map `LWKM_Frank_RunBinding_v01`:

```bat
BIND_RUN_SOURCES.cmd
```

De starter gebruikt de eerder bevestigde interpreter
`E:\tools\deltaforge\deltaforge_4\python.exe` en alleen de standaardbibliotheek.
Uitvoer: `LWKM_tools\LWKM_Frank_RunBinding_v01\run_source_binding.json`.
De optionele lokale fixturetests starten met `TEST_RUNBINDING.cmd`.
Bij gebruik vanuit de repository staat de starter onder `tools\lwkm_frank`.

## Resterend werk

Eerst de twaalf exacte bronbestanden uit het oorspronkelijke ZIP importeren en
tegen het bestaande SHA-register controleren. Daarna de centrale bronbinding
expliciet door de producenten laten gebruiken, met aparte nieuwe uitvoermappen
en regressie tegen de onaangeroerde Frank-referentie. Deze aanvulling maakt die
bronkeuze expliciet, maar koppelt de producenten nog niet aan de nieuwe binding.
Geen nieuwe productieberekening vrijgeven voordat die integratie en inhoudelijke
vergelijking daadwerkelijk zijn uitgevoerd.
