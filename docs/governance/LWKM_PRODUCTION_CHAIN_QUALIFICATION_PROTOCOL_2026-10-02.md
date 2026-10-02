# LWKM production-chain qualification protocol — 2026-10-02

## Doel

Dit document definieert de keten die stap voor stap moet worden vastgelegd, getest en toegelaten:

`LHM-server -> gekwalificeerde bronbestanden -> postprocessing -> SVAT -> HRU -> HRU-context -> DRA/BBC/MET -> SWP -> SWAP-runset`.

De keten is pas productiegeschikt wanneer:

1. ieder geconsumeerd bestand individueel gekwalificeerd is;
2. iedere transformatie een expliciet contract heeft;
3. iedere output herleidbaar is tot gekwalificeerde inputs, code en configuratie;
4. iedere stap zijn eigen regression/admission-gate heeft;
5. de volledige keten end-to-end is getest.

Project-wide file authority:
`docs/governance/LWKM_FILE_QUALIFICATION_POLICY_2026-10-02.md`.

LHM source provenance authority:
`docs/server/LHM_SOURCE_PROVENANCE_AND_COLLECTION_2026-10-02.md`.

## Ketenprincipe

Iedere stap heeft exact vijf elementen:

1. **Input authority**  
   Alleen gekwalificeerde bestanden of admitted outputs van de voorgaande stap.

2. **Transformation contract**  
   Wat de stap exact doet, inclusief units, ruimtelijke support, datumlogica, selectie- en fallbackregels.

3. **Output contract**  
   Welke bestanden ontstaan, met welke betekenis en identiteit.

4. **Qualification tests**  
   Structurele, semantische en numerieke controles.

5. **Admission gate**  
   Een expliciet PASS/FAIL-resultaat met persisted evidence.

Geen stap mag impliciet bestanden uit een andere map, oude workflow of handmatige tussenstap meenemen.

## Statuslabels

Gebruik per stap:

- `NOT_STARTED`
- `RECONSTRUCTED_NOT_QUALIFIED`
- `PARTIALLY_QUALIFIED`
- `QUALIFIED_NOT_ADMITTED`
- `PRODUCTION_ADMITTED`
- `BLOCKED_BY_PROVENANCE`
- `FALSIFIED`

Een stap is pas `PRODUCTION_ADMITTED` wanneer zowel de inputbestanden als de transformatie en outputs voldoen aan het contract.

---

# W00 — File qualification governance

## Doel

Zorgen dat geen onbekend of ongekwalificeerd bestand de productieketen binnenkomt.

## Input

Geen modelinput. Dit is een governance-gate.

## Contract

Elk geconsumeerd bestand heeft minimaal:
- logical ID;
- SHA-256;
- provenance;
- format contract;
- semantic contract;
- consumer;
- qualification evidence;
- status.

Afgeleide bestanden hebben daarnaast:
- parent identities;
- code commit;
- config version;
- transformation identity.

## Test

Automatische preflight moet ongekwalificeerde inputs afwijzen.

## Admission

`ZERO UNTRACED PRODUCTION INPUTS`.

## Huidige status

`QUALIFIED_NOT_ADMITTED`.

Beleid is vastgelegd, automatische handhaving moet nog onderdeel van de pipeline worden.

---

# W01 — LHM-server provenance freeze

## Doel

Van één expliciet geïdentificeerde LHM-run een immutable, gehashte bronset maken.

## Input

Authoritative server run tree.

## Contract

Q0:
- run/root identificeren.

Q1:
- source-spec uitvoeren;
- alle vereiste bestanden oplossen.

Q2:
- byte-identieke staging;
- per-file SHA-256.

Q3:
- manifest + metadata + ZIP.

Q4:
- fresh extraction;
- volledige hashverificatie.

## Output

`LHM_SOURCE_Q4_IMMUTABLE_SNAPSHOT`.

Inclusief:
- source ZIP;
- files.csv;
- collection.json;
- ZIP SHA-256;
- manifest SHA-256.

## Test

- geen ontbrekende required inputs;
- geen onopgeloste dubbelen;
- fresh extraction exact gelijk;
- geen stil toegevoegde afgeleide bestanden.

## Admission

`ZERO UNEXPLAINED FILE IDENTITY DIFFERENCES`.

## Huidige status

`NOT_STARTED_ON_REAL_SERVER`.

Procedure en draft source-spec bestaan.

---

# W02 — LHM postprocessing

## Doel

Ruwe LHM/MODFLOW-output deterministisch omzetten naar de derived grids die LWKM echt nodig heeft.

## Input authority

Alleen W01-admitted source files.

## Transformation contract

Python-target:
`tools/lhm_postprocess.py`.

Reeds gereconstrueerde semantiek:
- MODFLOW full-cell support = 62,500 m2;
- m3 -> mm: `sum(Q) / 62500 * 1000`;
- positief/negatief scheiden vóór temporele sommatie;
- state variables als tijdgemiddelde;
- geen impliciete resampling;
- geen stille NODATA-bewerkingen.

## Output

Versieerbare derived rasters met:
- parent source IDs;
- code commit;
- config ID;
- output SHA-256.

## Test

Golden regression op kleine echte serverperiode:
- geometry;
- NODATA;
- min/max;
- sum/mean;
- cel-voor-cel;
- max absolute error;
- hashes waar relevant.

## Admission

`ZERO UNEXPLAINED NUMERICAL DIFFERENCES`.

## Huidige status

`QUALIFIED_NOT_ADMITTED`.

Compatibility core is geïmplementeerd en getest; real-server golden regression ontbreekt.

---

# W03 — SVAT basis en selectie

## Doel

De exacte populatie SVATs en hun bronattributen definiëren die de LWKM/HRU-keten ingaan.

## Input authority

Gekwalificeerde W01/W02 outputs plus admitted static schematisation files.

## Belangrijke inputtypen

Onder andere:
- `svat.asc`;
- landbouw/natuurfilter;
- geometrie/header;
- landgebruik;
- bodem/BFE;
- soil2;
- uopp;
- irrigatie;
- AHN;
- rootzone;
- meteo-district;
- relevante grondwater/bottom-boundary-attributen.

## Contract

Expliciet vastleggen:
- welke SVATs actief zijn;
- welke landbouw/natuur zijn;
- wat de betekenis is van uitgesloten cellen;
- hoe de bekende vier LWKM/LWKM2-cellen worden behandeld;
- geen extra historische filter aannemen zonder evidence.

## Output

Gekwalificeerde SVAT-populatie met stabiele IDs en source lineage.

## Test

- populatiecount;
- geometry alignment;
- unique IDs;
- filter reproduction;
- vergelijking met historische accepted population.

## Admission

`SVAT_POPULATION_PRODUCTION_ADMITTED`.

## Huidige status

`RECONSTRUCTED_NOT_QUALIFIED`.

Hoofdsemantiek is grotendeels bekend; formele file-level input qualification en end-to-end population gate moeten nog worden uitgevoerd vanaf W01.

---

# W04 — Suspect/rest donor assignment

## Doel

Voor verdachte/problematische cellen exact vastleggen welke donor wordt gebruikt en waarom.

## Input authority

Admitted SVAT-populatie plus gekwalificeerde suspect-inputs.

## Contract

Drie concepten blijven strikt gescheiden:

1. legacy `svat_donor`;
2. operationele Piet-R-procedure / `hru_cluster_donor_svat`;
3. `hru_representative_svat`.

De historische `verdacht.asc` is run-bound provenance en niet automatisch moderne physical authority.

## Output

Donor-assignment table met:
- target SVAT;
- donor SVAT;
- assignment reason;
- algorithm/version;
- parent source IDs.

## Test

- deterministische rerun;
- geen missing targets;
- geen self/invalid mappings behalve expliciet toegelaten;
- historische vergelijking waar oracle beschikbaar is.

## Admission

`DONOR_ASSIGNMENT_PRODUCTION_ADMITTED`.

## Huidige status

`PARTIALLY_QUALIFIED`.

Piet's R-procedure is operationeel authority voor reconstructie, maar de volledige moderne file-qualified route moet nog in de keten worden opgenomen.

---

# W05 — HRU constructie

## Doel

Van admitted SVATs een reproduceerbare HRU-schematisatie maken.

## Input authority

W03 + W04 admitted outputs.

## Contract

Expliciet vastleggen:
- HRU clustering/classificatie;
- membership;
- area/support;
- natuur/landbouwstatus;
- representatieve SVAT;
- donor-informatie;
- relevante static attributes.

## Output

Een authoritative HRU-membership/context basis, onder andere:
- HRU -> SVAT membership;
- HRU -> representative SVAT;
- HRU-level attributes.

## Test

- exact aantal HRUs;
- membership completeness;
- every SVAT exactly expected number of memberships;
- area closure;
- deterministic rerun;
- known corrections.

## Admission

`HRU_SCHEMATISATION_PRODUCTION_ADMITTED`.

## Huidige status

`PARTIALLY_QUALIFIED`.

De huidige 10,242-run context kan volledig worden opgebouwd, maar deze stap moet nog als volledige provenance-driven transformatie worden gesloten.

---

# W06 — HRU datamodel/context assembly

## Doel

Alle gekwalificeerde HRU-attributen en lookups samenbrengen tot typed execution contexts.

## Input authority

Admitted HRU outputs plus qualified lookup tables.

## Belangrijke inputs

Onder andere:
- `Datamodel_10242.xlsx`;
- BOFEK lookup;
- horizon lookup;
- soil/landuse/crop lookup;
- corrected soil2/crop mappings;
- representative-SVAT records.

## Contract

Typed joins, explicit required fields, no silent fallback.

## Output

10,242 typed run contexts.

## Test

Reeds gekwalificeerd:
- 22 worksheets;
- 10,242 Runs;
- 10,242 typed contexts;
- zero unresolved joins/required-field issues.

## Admission

`HRU_CONTEXT_10242_PRODUCTION_ADMITTED`.

## Huidige status

`QUALIFIED_NOT_ADMITTED`.

Ingestie/context gate is gesloten; volledige upstream W01-W05 lineage moet nog aan de context worden gekoppeld.

---

# W07 — DRA generation

## Doel

Per HRU een gekwalificeerd drainagebestand genereren.

## Input authority

Admitted HRU context + qualified drainage source files.

## Modern production contract

- deterministic all-member aggregation;
- 62,500 m2 full MODFLOW cell support per member;
- representative-SVAT dqsat;
- qualified conductance/infiltration/bottom/level inputs;
- geen undefined-state emulatie;
- geen oracle force-fitting.

## Output

Per HRU één DRA plus provenance record.

## Tests

- parser completeness;
- DRARES;
- INFRES;
- ZBOTDR;
- SWALLO;
- L;
- alle seasonal LEVEL rows;
- no extra/missing assignments;
- 49-run regression;
- mass/geometry semantics waar relevant.

Bekend:
- 75 `L` differences zijn preregistered modern-vs-historical;
- overige verschillen mogen niet automatisch intentional worden.

## Admission

`ZERO UNEXPLAINED DRA DIFFERENCES` buiten preregistered modern corrections.

## Huidige status

`BLOCKED_BY_PROVENANCE`.

Historische producer/input binding en de drie lengte-rasters ontbreken nog.

---

# W08 — BBC generation

## Doel

Per HRU de juiste bottom-boundary configuratie genereren.

## Input authority

Qualified HRU context + admitted bottom-boundary source files/postprocessing.

## Contract

Nog volledig als productiecontract uit te schrijven, waaronder:
- qmodf/FLF/QLAT ownership;
- correction grid/table semantics;
- VC/KD gebruik;
- free drainage versus groundwater-linked routes;
- tijdsdekking/restarts.

## Output

Per HRU BBC plus lineage.

## Test

- historische regressioncases;
- sign/units;
- temporal coverage;
- no missing period;
- known Flevoland correction;
- cell/HRU aggregation closure.

## Admission

`BBC_PRODUCTION_ADMITTED`.

## Huidige status

`RECONSTRUCTED_NOT_QUALIFIED`.

Historische semantiek is gedeeltelijk gereconstrueerd; formele gate moet nog worden uitgewerkt.

---

# W09 — MET generation

## Doel

Per HRU reproduceerbare SWAP-meteoinvoer genereren.

## Input authority

Qualified meteorological basis + district assignment + period definitions.

## Contract

Onder andere:
- station/district mapping;
- Tmin/Tmax/Tavg;
- wind;
- humidity;
- radiation;
- precipitation;
- WET semantics;
- period/date coverage.

## Output

Per HRU MET plus lineage.

## Test

- complete daily coverage;
- station mapping;
- historical regression;
- WET edge cases, inclusief P=0;
- units/format.

## Admission

`MET_PRODUCTION_ADMITTED`.

## Huidige status

`RECONSTRUCTED_NOT_QUALIFIED`.

---

# W10 — Direct SWP rendering

## Doel

Uit een typed HRU-context rechtstreeks de volledige SWP input renderen zonder trage/fragiele tussenstappen.

## Input authority

Admitted W06 context plus admitted templates/mappings and references to W07-W09 outputs.

## Contract

- expliciet versioned SWP profile;
- exact active tables/assignments;
- geen guessed historical template;
- modern profile mag afwijken, maar alleen expliciet/versioned.

## Output

Per HRU `swap.swp`.

## Test

49-run full active-SWP semantic regression.

Gate:
- comparator must cover every active table/assignment;
- only preregistered differences accepted;
- zero unexplained differences.

## Admission

`DIRECT_SWP_RENDERER_ADMITTED`.

## Huidige status

`BLOCKED_BY_PROVENANCE`.

Exact historical `swap_wwl.swp` is nog niet recovered. Current `wwl.swp` is een andere incompatibele versie.

---

# W11 — Per-HRU package assembly

## Doel

Alle admitted componenten samenbrengen tot één complete SWAP-run directory.

## Input authority

Alleen production-admitted:
- SWP;
- DRA;
- BBC;
- MET;
- overige expliciet vereiste assets.

## Output

Immutable HRU run package met eigen manifest.

## Test

- all referenced files exist;
- hashes match registry;
- no undeclared files consumed;
- SWAP input parser accepts package;
- deterministic rebuild gives same manifest/hashes.

## Admission

`HRU_RUN_PACKAGE_ADMITTED`.

## Huidige status

`NOT_STARTED_AS_FORMAL_GATE`.

Historische 49-run directories fungeren als oracle, niet als moderne package authority.

---

# W12 — 49-run integrated regression

## Doel

De complete moderne keten op de bestaande 49 historische oracle-runs toetsen.

## Input authority

W11 packages generated from admitted upstream steps.

## Tests

Per run:
- SWP semantics;
- DRA semantics;
- BBC semantics;
- MET semantics;
- referenced assets;
- SWAP startup/smoke;
- intentional-difference registry.

## Admission

`49_RUN_INTEGRATED_REGRESSION_ADMITTED`.

Voorwaarden:
- zero unexplained differences;
- iedere intentional difference preregistered en source-backed.

## Huidige status

`PARTIALLY_QUALIFIED`.

Losse subgates bestaan, maar de volledige keten is nog niet vanuit één admitted source graph opgebouwd.

---

# W13 — 10,242-run production build

## Doel

De complete huidige LWKM-populatie genereren.

## Input authority

Alle upstream stappen production-admitted.

## Output

10,242 complete HRU run packages.

## Test

- exact run count;
- no unresolved context;
- all file identities qualified;
- no missing references;
- deterministic rebuild;
- aggregate QA/statistics;
- representative SWAP smoke subset;
- eventually full production execution as required.

## Admission

`LWKM_10242_BUILD_ADMITTED`.

## Huidige status

`NOT_STARTED_AS_ADMISSION_GATE`.

---

# W14 — End-to-end production admission

## Doel

Aantonen dat de volledige keten reproduceerbaar, traceerbaar en operationeel is.

## Required graph

`W01 -> W02 -> W03 -> W04 -> W05 -> W06 -> W07/W08/W09 -> W10 -> W11 -> W12 -> W13`.

## Eindtest

Voor iedere finale run moet recursief aantoonbaar zijn:

`final file -> producing transformation -> qualified parent files -> immutable LHM source snapshot`.

## Admission invariants

- `100% OF CONSUMED FILE IDENTITIES QUALIFIED`;
- `ZERO UNTRACED PRODUCTION INPUTS`;
- `ZERO UNEXPLAINED REGRESSION DIFFERENCES`;
- `DETERMINISTIC REBUILD UNDER SAME SOURCE+CODE+CONFIG`.

## Huidige status

`NOT_STARTED`.

---

# Werkvolgorde vanaf nu

De keten wordt vanaf links naar rechts gesloten.

Niet verder springen dan nodig.

Praktische volgorde:

1. W01 echte server-run vastleggen en Q0-Q4 uitvoeren;
2. W02 kleine server golden regression;
3. W03 SVAT-populatie formeel kwalificeren;
4. W04 donor/suspect-route kwalificeren;
5. W05 HRU-schematisatie kwalificeren;
6. W06 typed context aan volledige lineage binden;
7. W07 DRA sluiten;
8. W08 BBC sluiten;
9. W09 MET sluiten;
10. W10 SWP sluiten;
11. W11 packaging;
12. W12 49-run integrated;
13. W13 10,242-run build;
14. W14 end-to-end admission.

## Governance-besluit

Vanaf nu wordt iedere volgende werksessie aan één of meer van deze W-stappen gekoppeld.

Een stap wordt pas overgeslagen wanneer zijn admission evidence al expliciet bestaat.

De keten is niet klaar omdat de code bestaat. De keten is klaar wanneer elke stap aantoonbaar gekwalificeerd en admitted is.
