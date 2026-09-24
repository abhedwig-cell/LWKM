# Notitie: workflow van LHM naar SWAP via de HRU-systematiek

**Project:** LWKM 2.0  
**Status:** geactualiseerde conceptwerknotitie, 24 september 2026  
**Doel:** de volledige route van LHM-resultaten naar gekwalificeerde SVAT-informatie, HRU-afleiding, SWAP-invoer en SWAP-resultaten als één beheersbaar, reproduceerbaar en inhoudelijk toetsbaar proces vastleggen.

## 1. Aanleiding

De huidige LWKM-werkwijze is in de loop van meerdere jaren stapsgewijs opgebouwd. Daardoor staan brondata, scripts, selectieregels, correcties, HRU-afleiding, SWAP-invoer, rekentaken en nabewerking nu op verschillende plekken en deels in verschillende beheeromgevingen.

Dat is verklaarbaar vanuit de ontwikkeling van het onderzoek, maar maakt het moeilijk om achteraf exact vast te stellen:

- welke LHM-resultaten als basis zijn gebruikt;
- welke ruimtelijke selectie is toegepast;
- welke hydrologische correcties zijn uitgevoerd;
- welke SVATs als hydrologisch verdacht zijn aangemerkt;
- hoe met zulke verdachte SVATs is omgegaan;
- welke exacte SVAT-toestand voor HRU-afleiding is gebruikt;
- of dezelfde SVAT-toestand vervolgens voor SWAP-invoer is gebruikt;
- hoe HRU-eigenschappen naar SWAP-invoer zijn vertaald;
- welke bestanden werkelijk naar de rekeneenheid zijn gestuurd;
- welke resultaten terugkwamen en hoe die zijn nabewerkt;
- en vooral: welk deel van de uiteindelijke hydrologische verandering door welke stap wordt veroorzaakt.

Daarom wordt de bestaande keten nu niet alleen gereconstrueerd, maar tegelijk opnieuw ingericht als één gecontroleerde workflow.

De nieuwe aanpak kent twee doelen:

1. **reconstructie van de huidige LWKM 2.0-keten**, zodat bestaande resultaten kunnen worden verantwoord en inconsistenties kunnen worden opgespoord;
2. **een canonical workflow**, die voorschrijft hoe volgende runs reproduceerbaar, versieerbaar en inhoudelijk toetsbaar worden uitgevoerd.

## 2. Hoofdprincipe

De belangrijkste ontwerpregel is:

> **De workflow wordt als één end-to-end proces beheerd, ook als de berekeningen fysiek op verschillende systemen worden uitgevoerd.**

De keten mag dus organisatorisch uit meerdere werkplekken bestaan, maar wetenschappelijk niet uit losse, moeilijk herleidbare deelprocessen.

Iedere hoofdtransitie krijgt daarom:

- een expliciete input-authority;
- een expliciet outputproduct;
- een versieerbare configuratie;
- vastgelegde software/code;
- een QA-gate;
- een manifest met run-id en checksums;
- een overdrachtsmoment waarop gecontroleerd wordt dat de juiste bestanden worden gebruikt.

## 3. Afbakening

De volledige LHM-berekening zelf valt buiten deze workflow. Het formele startpunt is een gecontroleerde export uit een afgeronde LHM-run op de NHI/LHM-server.

Het formele eindpunt is een gecontroleerd SWAP-resultaat en een reproduceerbaar overdrachtspakket richting de volgende LWKM-stap, waaronder ANIMO.

De gedistribueerde rekeneenheid waarop grote aantallen SWAP-runs worden uitgevoerd wordt vooralsnog als externe uitvoeringsomgeving behandeld, maar de invoer ernaartoe en de resultaten die terugkomen horen nadrukkelijk wel bij de workflow.

De hoofdroute is:

```text
LHM-run op NHI/LHM-server
        │
        ▼
LHM_EXPORT
        │
        ▼
SVAT_NL_BASE
        │
        ▼
SVAT_LBN
        │
        ▼
SVAT_FLEVOLAND_CORR
        │
        ▼
SVAT_QUALIFIED
        │
        ├──────────────► HRU_DERIVATION
        │                    │
        │                    ├─ SVAT_HRU_MAP
        │                    ├─ HRU_SCHEMA
        │                    └─ representatieve SVAT
        │
        └──────────────────────────────────┐
                                           │
                           gedeelde SVAT-authority
                                           │
                                           ▼
                                  SWAP_INPUT_BUILD
                                      ├─ HRU-SWAP
                                      └─ representatieve-SVAT SWAP
                                           │
                                           ▼
                                  gedistribueerde SWAP-run
                                           │
                                           ▼
                                      SWAP_OUTPUT
                                           │
                                           ▼
                                  SWAP_POSTPROCESSING
                                           │
                                           ▼
                                       QA + analyse
                                           │
                                           ▼
                                overdracht richting ANIMO
```

De datastroom is lineair, maar de ontwikkeling is iteratief. Een afwijkend resultaat kan aanleiding zijn om terug te gaan naar een eerdere stap. Een wijziging levert dan een nieuwe kandidaatversie op. Bestaande geaccepteerde resultaten worden niet stilzwijgend overschreven.

## 4. Stap 1: gecontroleerde export uit LHM

Op de LHM-server is veel meer modeluitvoer beschikbaar dan LWKM downstream nodig heeft. Het is daarom niet wenselijk om de volledige LHM-run als werkpakket mee te slepen.

Er wordt een formeel **LHM_EXPORT-pakket** gedefinieerd waarin alleen gegevens worden opgenomen die downstream aantoonbaar nodig zijn.

Daarin zitten onder meer:

- SVAT-identiteit en ruimtelijke ligging;
- GHG en GLG;
- relevante waterbalanscomponenten;
- kwel en wegzijging;
- drainage en ontwatering;
- runoff;
- infiltratie en beregening;
- relevante MetaSWAP- en MODFLOW-grootheden;
- tijdsafhankelijke MODFLOW-informatie voor SWAP-randvoorwaarden;
- noodzakelijke statische gegevens en classificaties.

Per exportproduct worden minimaal vastgelegd:

- LHM-versie/run;
- periode;
- eenheid;
- tekenconventie;
- oppervlaktebasis;
- bronbestand;
- producerend script;
- checksum.

De grens wordt daarmee expliciet:

> **LHM is upstream authority; LWKM begint bij een gecontroleerde en reproduceerbare export.**

## 5. Stap 2: technische ruimtelijke afbakening

Niet alle LHM-cellen zijn relevant voor de inhoudelijke LWKM-analyse.

Een eerste technische ruimtelijke afbakening verwijdert onder meer:

- buitenlandse cellen;
- grote of open oppervlaktewateren buiten het relevante Nederlandse modeldomein;
- overige ballast die inhoudelijk niet wordt meegenomen.

Deze stap levert:

**`SVAT_NL_BASE`**

Dit is de Nederlandse hydrologische basis na alleen technische afbakening.

Belangrijk is dat deze stap niet wordt verward met de daaropvolgende inhoudelijke selectie op landbouw en natuur.

## 6. Stap 3: inhoudelijke selectie landbouw + natuur

De stap van geheel Nederland naar alleen landbouw en natuur is inhoudelijk relevant en kan de landelijke waterbalans duidelijk beïnvloeden.

Daarom wordt deze selectie als zelfstandige transformatie bewaard en geanalyseerd.

Output:

**`SVAT_LBN`**

De hydrologische waarden van behouden SVATs veranderen door deze stap niet. Het effect ontstaat doordat de populatie en het vertegenwoordigde oppervlak veranderen.

De vergelijking:

**`SVAT_NL_BASE → SVAT_LBN`**

wordt expliciet gerapporteerd als:

**effect van selectie landbouw + natuur**.

## 7. Stap 4: Flevoland als hydrologische correctie

De correctie voor Flevoland is niet langer alleen als mogelijke “kwelcorrectie” beschreven.

Het onderliggende probleem is dat diepe waterlopen die fysiek door de deklaag heen steken in de modelschematisatie deels zodanig kunnen worden voorgesteld dat diep grondwater eerst via de bovenste laag wordt gerouteerd en daarna via ontwatering wordt afgevoerd.

Daardoor kan de standaard LHM-run een tussenstap zichtbaar maken die fysisch voor de downstream toepassing niet gewenst is.

De alternatieve Flevoland-berekening levert daarom een gecorrigeerde hydrologische toestand.

Belangrijk is dat daarbij niet alleen naar kwel wordt gekeken. Ook gekoppelde componenten kunnen veranderen, bijvoorbeeld:

- ontwatering;
- drainage;
- andere oppervlaktewaterfluxen;
- bergingsverandering;
- mogelijk GHG/GLG of andere balanscomponenten.

De correcte aanpak is daarom:

**`SVAT_LBN`**  
→ toepassen van de geaccepteerde Flevoland-correctie  
→ **`SVAT_FLEVOLAND_CORR`**

De structuur, SVAT-sleutels, periode, eenheden en oppervlaktebasis blijven gelijk.

De vergelijking:

**`SVAT_LBN → SVAT_FLEVOLAND_CORR`**

is daarmee het zuivere **effect van de Flevoland-correctie**.

De precieze huidige authority van deze correctie moet nog worden gereconstrueerd. Daarbij moet worden vastgesteld welke balanscomponenten uit de alternatieve LHM-run daadwerkelijk moeten worden overgenomen.

## 8. Stap 5: hydrologische kwalificatie en behandeling van extremen

Na de Flevoland-correctie volgt de inhoudelijke beoordeling van hydrologisch verdachte SVATs.

In de huidige scripts bestaan al regels voor situaties zoals:

- zeer hoge kwel;
- sterke wegzijging;
- hoge runoff;
- hoge subinfiltratie;
- kwel bij droge grondwaterstanden;
- GHG boven maaiveld bij landbouw;
- specifieke combinaties van hydrologische toestanden en fluxen.

Deze regels worden voortaan niet meer alleen verspreid in batchfiles of analysecode beheerd, maar als expliciete **kennisregels**.

Iedere kennisregel krijgt minimaal:

- rule-id;
- versie;
- beschrijving;
- exacte formule;
- variabelen;
- eenheid;
- periode;
- toepassingsgebied;
- eventuele uitzonderingsgebieden;
- ernstklasse;
- verwachte actie;
- inhoudelijke onderbouwing;
- status.

Een belangrijke ontwerpregel is:

> **signaleren is niet hetzelfde als vervangen.**

Een SVAT die een regel overschrijdt krijgt in eerste instantie een **FLAG**. Daarna wordt onderzocht of het gaat om:

- een fysisch bijzondere situatie;
- een fout of beperking in de LHM-brondata;
- een fout in de verwerking;
- een uitzonderingsgebied;
- of een kennisregel die aangepast moet worden.

Pas daarna wordt vastgelegd of de SVAT:

- volledig bruikbaar blijft;
- voor een specifieke downstream toepassing niet mag meetellen;
- via een donor of andere regel moet worden vervangen.

De output van deze stap is:

**`SVAT_QUALIFIED`** of, voor effectanalyse, **`SVAT_QUALIFIED_REP`**.

De vergelijking:

**`SVAT_FLEVOLAND_CORR → SVAT_QUALIFIED_REP`**

is het zuivere **effect van het extremen-/kwalificatiebeleid**.

## 9. Eén gedeelde SVAT-authority

Dit is een harde ontwerpregel voor de verdere keten:

> **Dezelfde gekwalificeerde SVAT-informatie vormt de basis voor zowel de HRU-afleiding als de opbouw van SWAP-invoer.**

Er mag dus niet één SVAT-bestand worden gebruikt voor HRU-afleiding en later een andere, verondersteld equivalente kopie voor SWAP-input.

Dit betekent dat HRU-afleiding en SWAP-opbouw aantoonbaar dezelfde:

- run-id;
- SVAT-versie;
- correctiestatus;
- kwalificatieregels;
- checksums;
- configuratie

moeten gebruiken.

Voor de huidige HRU10242-lijn is dit nog een belangrijk open reconstructiepunt.

Er moet worden vastgesteld:

- welk exact SVAT-bestand Piet gebruikte voor HRU10242;
- of de Flevoland-correctie daarin al was verwerkt;
- of behandeling van hydrologische extremen daarin al aanwezig was;
- en of de latere SWAP-inputopbouw exact dezelfde SVAT-toestand gebruikte.

Zolang dat niet is bevestigd, is de huidige HRU10242 → SWAP-lijn nog niet volledig consistency-qualified.

## 10. Stap 6: HRU-afleiding

Na kwalificatie volgt een zelfstandige HRU-procedure.

De actuele authority voor deze werkstroom is **HRU10242**.

De huidige HRU-methode combineert onder meer:

- bodem;
- landgebruik;
- hydrologische kenmerken;
- clustering op GHG en netto kwel;
- minimale groepsgrootte;
- spreidings-/MAE-controles;
- donor-matching;
- selectie van een representatieve SVAT per HRU.

De belangrijkste outputproducten zijn:

- **SVAT_HRU_MAP:** koppeling van iedere SVAT aan een HRU;
- **HRU_SCHEMA:** eigenschappen per HRU;
- representatieve SVAT;
- HRU-raster;
- kwaliteitsinformatie zoals purity en afwijkingen in GHG/netto kwel.

De HRU-procedure verandert de SVAT-basis niet, maar legt een nieuwe representatielaag over dezelfde gekwalificeerde SVAT-populatie.

## 11. Stap 7: twee SWAP-representaties

Vanuit dezelfde `SVAT_QUALIFIED` authority en de HRU-resultaten willen we twee SWAP-representaties kunnen opbouwen.

### 11.1 HRU-SWAP

Voor iedere HRU wordt één SWAP-model opgebouwd uit informatie van alle SVATs binnen de HRU.

Daarvoor worden expliciete regels gebruikt voor onder andere:

- bodem;
- landgebruik;
- worteldiepte;
- drainage;
- meteorologie;
- onderrand;
- hydrologische aggregatie;
- fallbackgedrag.

### 11.2 Representatieve-SVAT SWAP

Daarnaast wordt per HRU een SWAP-model opgebouwd voor de representatieve SVAT die tijdens de HRU-afleiding is gekozen.

Deze route is inhoudelijk belangrijk omdat daarmee een schonere vergelijking mogelijk wordt tussen:

- LHM voor een concrete SVAT;
- SWAP voor diezelfde representatieve SVAT.

Beide routes moeten reproduceerbaar zijn en kunnen downstream gebruikt worden voor analyse en, waar gewenst, overdracht richting ANIMO.

## 12. SWAP_MAPPING als expliciete configuratie

De bestaande `HRUlist2SWAP`-code bevat veel inhoudelijke mappingregels.

Die mogen niet uitsluitend verborgen blijven in Fortran-code.

Per SWAP-invoerveld wordt voortaan expliciet vastgelegd:

- uit welk bronproduct het veld komt;
- welke SVATs meetellen;
- of een representatieve SVAT wordt gebruikt;
- welke aggregatieregel geldt;
- welke eenheidsconversie plaatsvindt;
- welke fallback geldt;
- welke configuratieversie is gebruikt.

Deze configuratie vormt de **SWAP_MAPPING**.

## 13. Stap 8: gedistribueerde SWAP-run

De grote aantallen SWAP-berekeningen worden uitgevoerd op een gedistribueerde rekeneenheid.

De interne werking daarvan kan voorlopig buiten de hoofdreconstructie blijven, maar de stap zelf moet zichtbaar en controleerbaar in de keten staan.

De overdracht naar de rekeneenheid bevat minimaal:

- immutable SWAP-inputpakket;
- runmanifest;
- runlijst;
- checksums;
- SWAP-versie/executable;
- configuratieversies.

De terugkomst bevat minimaal:

- resultaatpakket;
- completion/status-overzicht;
- logs;
- checksums;
- run-id.

Daarmee kan worden gecontroleerd dat het ontvangen resultaat exact hoort bij het verstuurde SWAP-inputpakket.

## 14. Stap 9: SWAP-postprocessing

De teruggekomen SWAP-uitvoer wordt momenteel onder andere door Leo nabewerkt tot compacte CSV-bestanden waarmee hydrologische analyses kunnen worden uitgevoerd.

Ook deze stap hoort expliciet bij de workflow.

Daarom moeten worden vastgelegd:

- welk SWAP-resultaatpakket is verwerkt;
- welk script is gebruikt;
- welke variabelen worden samengevat;
- welke aggregatieregels gelden;
- welke uitvoer-CSV is geproduceerd;
- welke run-id daarbij hoort.

## 15. Hydrologische QA als vaste reeks gates

Versiebeheer en provenance zijn noodzakelijk, maar niet voldoende.

Op meerdere plekken in de keten komt daarom een inhoudelijke QA-gate.

### 15.1 SVAT_BASE QA

Controle op de aangeleverde LHM/SVAT-hydrologie vóór downstream besluiten.

### 15.2 SVAT_QUALIFIED QA

Toetsing aan versieerbare hydrologische kennisregels.

### 15.3 HRU QA

Controle of de HRU-representatie voldoende overeenkomt met de onderliggende gekwalificeerde SVAT-populatie.

### 15.4 SWAP input QA

Controle of gegenereerde SWAP-invoer:

- uit de juiste authority komt;
- binnen afgesproken grenzen ligt;
- geen onmogelijke combinaties bevat.

### 15.5 SWAP output QA

Controle op:

- runstatus;
- waterbalans;
- hydrologische plausibiliteit;
- afwijkende HRU's;
- afwijking ten opzichte van de upstream referentie;
- ruimtelijke uitschieters;
- verandering ten opzichte van de vorige geaccepteerde run.

Een afwijking wordt niet stilzwijgend verwijderd, maar komt in een machineleesbaar **exception register**.

## 16. Hydrologische vergelijking in vijf toestanden

Voor de inhoudelijke effectanalyse worden vijf vergelijkbare toestanden onderscheiden.

| Toestand | Betekenis |
|---|---|
| **S0 SVAT_NL_BASE** | Nederland na technische ruimtelijke afbakening |
| **S1 SVAT_LBN** | landbouw + natuur |
| **S2 SVAT_FLEVOLAND_CORR** | idem, met Flevoland-correctie |
| **S3 SVAT_QUALIFIED_REP** | idem, met behandeling van hydrologische extremen |
| **S4 HRU10242** | HRU-representatie van S3 |

Daarmee ontstaan vier afzonderlijk toewijsbare effecten:

1. **S0 → S1:** effect selectie landbouw + natuur;
2. **S1 → S2:** effect Flevoland-correctie;
3. **S2 → S3:** effect extremen-/kwalificatiebeleid;
4. **S3 → S4:** effect HRU-representatie.

Dit is belangrijk voor de inhoudelijke communicatie richting Deltares.

De uiteindelijke afwijking tussen LHM en HRU mag niet als één gecombineerd effect worden gepresenteerd. Er moet zichtbaar worden gemaakt welk deel voortkomt uit:

- selectie van het domein;
- correcties in de LHM-hydrologie;
- behandeling van niet-plausibele LHM-resultaten;
- en pas daarna uit de HRU-schematisatie zelf.

## 17. Terugprojectie van HRU naar SVAT-niveau

Om het HRU-effect zuiver te kunnen bepalen, worden HRU-waarden teruggeprojecteerd naar de oorspronkelijke SVAT-locaties.

Conceptueel:

```text
SVAT → HRU → HRU-waarde terugzetten op iedere member-SVAT
```

Doelproduct:

**`SVAT_HRU10242_BACKPROJECTED`**

Daardoor kunnen S3 en S4 worden vergeleken op:

- dezelfde SVAT-sleutels;
- dezelfde ruimtelijke ondersteuning;
- dezelfde oppervlaktebasis.

Dit maakt niet alleen landelijke analyse mogelijk, maar ook regionale en ruimtelijke analyse.

## 18. Landelijke én regionale effectanalyse

Landelijke totalen zijn onvoldoende.

Positieve en negatieve lokale verschillen kunnen elkaar op landelijke schaal compenseren.

Daarom worden per overgang minimaal bepaald:

- gebiedsgewogen landelijk totaal of gemiddelde;
- absoluut verschil;
- relatief verschil;
- MAE;
- RMSE;
- percentielen van lokale verschillen;
- maximale absolute afwijking;
- beïnvloed oppervlak;
- regionale samenvattingen;
- ruimtelijke kaarten van de verandering.

De regionale indeling moet stabiel en versieerbaar zijn.

Mogelijke aggregaties zijn bijvoorbeeld:

- waterbeheergebied;
- LHM-district;
- provincie;
- landbouwgebied;
- andere afgesproken rapportagegebieden.

## 19. Opslag, werkplekken en authority

De workflow wordt fysiek op meerdere plekken uitgevoerd.

### NHI/LHM-server

Rol:
- upstream LHM-berekening;
- productie van het gecontroleerde LHM_EXPORT-pakket.

### W:-schijf

Rol:
- duurzame projectdocumentatie;
- geaccepteerde configuraties;
- manifests;
- canonical kleine/middelgrote producten;
- QA/evidence;
- belangrijke bron- en interfacebestanden waar opslag dat toelaat.

De W:-schijf hoeft niet alle grote tussenproducten te bevatten.

### Leo-omgeving

Rol:
- grote werk- en stagingomgeving;
- datatransfer;
- raster- en gridverwerking;
- opbouw van SVAT/HRU/SWAP-invoer;
- grote tijdelijke tussenproducten;
- SWAP-postprocessing.

Deze omgeving is een rekencentrum/werkruimte, niet automatisch de wetenschappelijke authority.

### GitHub

Repository:

`abhedwig-cell/LWKM`

Rol:
- broncode;
- scripts;
- configuraties;
- workflowdocumentatie;
- manifests/templates;
- QA-regels;
- kleine evidenceproducten;
- provenance.

Grote modeldata hoeven niet in Git.

## 20. Authority versus working copy

Niet ieder bestand heeft dezelfde status.

We onderscheiden:

### SOURCE_AUTHORITY

Extern of upstream geproduceerd bronbestand dat bewaard moet blijven.

Voorbeelden:
- geaccepteerde LHM-export;
- alternatieve Flevoland-export;
- noodzakelijke statische basisdata.

### CANONICAL_PRODUCT

Geaccepteerd resultaat van een reproduceerbare LWKM-transformatie.

Voorbeelden:
- geaccepteerde `SVAT_QUALIFIED`;
- HRU10242-schema;
- geaccepteerde SWAP-inputrelease.

### WORKING_COPY

Tijdelijke kopie voor verwerking.

Een working copy mag nooit alleen vanwege zijn locatie of datum productieauthority worden.

### EVIDENCE

QA-rapporten, vergelijkingstabellen, exception registers en logs die aantonen waarom een kandidaatversie is geaccepteerd of afgewezen.

## 21. Overdracht als formeel handoffpunt

Een bestand is niet correct overgedragen omdat iemand weet dat het “daar staat”.

Een handoff is pas compleet wanneer:

1. bronrun of bronpakket is geïdentificeerd;
2. de verwachte bestanden in een manifest staan;
3. de bestanden fysiek aanwezig zijn;
4. checksums overeenkomen;
5. schema/metadata/basic geometry zijn gecontroleerd;
6. de ontvangende stap registreert welke exacte inputversie is gebruikt.

De volgende stap mag alleen lezen uit een geaccepteerd pakket.

## 22. Geen kopieën-van-kopieën als productiebron

Productiescripts mogen niet afhankelijk zijn van een bestand dat toevallig in een lokale directory staat met een herkenbare naam.

Daarom worden runs/pakketten benoemd met een expliciete id, bijvoorbeeld:

```text
LHM43-1991_2020-EXPORT-001
LWKM20-SVAT-QUAL-003
LWKM20-HRU10242-001
LWKM20-SWAPINPUT-HRU10242-004
LWKM20-SWAPOUTPUT-HRU10242-004
```

Een eventuele alias `current` mag alleen verwijzen naar zo'n vaste run-id. De feitelijk gebruikte run-id wordt altijd in het manifest opgeslagen.

## 23. Wat moet blijvend worden opgeslagen?

Niet ieder groot afgeleid bestand hoeft voor altijd te worden bewaard als het reproduceerbaar opnieuw kan worden opgebouwd.

Dat mag alleen wanneer:

- de authoritative input bewaard is;
- code en configuratie bewaard zijn;
- executable-versies bekend zijn;
- de transformatie reproduceerbaar is;
- outputmanifesten bestaan;
- QA/evidence voor de geaccepteerde run is bewaard.

Als een van deze voorwaarden niet is voldaan, moet het betreffende product voorlopig als authority worden behandeld en bewaard blijven.

## 24. Versiebeheer en wijzigingslus

Voor iedere kandidaat- of productierun wordt een manifest gebruikt met minimaal:

- input run-id;
- inputbestanden en checksums;
- LHM-versie;
- codecommit;
- configuratieversies;
- HRU-versie;
- SWAP-versie;
- outputlocaties;
- QA-status.

De ontwikkellus wordt:

**OBSERVE → LOCALIZE → PROPOSE → CANDIDATE RUN → COMPARE → ACCEPT/REJECT → PERSIST**

De basisregel is:

> **Geen getal in een canonical product verandert zonder dat zichtbaar is welke input, configuratie, code of expliciete correctie is gewijzigd.**

## 25. Huidige stand van zaken

De reconstructie heeft inmiddels het volgende opgeleverd:

- de globale end-to-end LHM → SVAT → HRU → SWAP-keten is gereconstrueerd;
- een canonical workflow is vastgelegd;
- een concept LHM-exportcontract bestaat;
- de huidige 75-koloms SVAT-interface uit `LWKM_makeHRU v0.20` is gedocumenteerd;
- HRU10242 is als actuele HRU-authority gekozen;
- de HRU-clusteringsmethodiek is technisch beschreven;
- de huidige `HRUlist2SWAP v0.38`-mapping is grotendeels veld voor veld gereconstrueerd;
- bestaande hydrologische kwalificatieregels zijn teruggevonden en als versieerbare kennislaag in ontwerp gebracht;
- de Flevoland-correctie is als afzonderlijke hydrologische correctiestap gedefinieerd;
- de vijfstappenvergelijking voor hydrologische effecttoerekening is vastgelegd;
- de eis van één gedeelde `SVAT_QUALIFIED` authority voor HRU én SWAP is expliciet gemaakt;
- twee SWAP-routes zijn gedefinieerd: HRU-SWAP en representatieve-SVAT SWAP;
- hydrologische QA-gates en een exception-registerconcept zijn vastgelegd;
- opslag-, werkplek- en handoffarchitectuur is beschreven;
- een runmanifest, wijzigingsprocedure en effect-accountingstructuur bestaan;
- een eerste QA-tool is toegevoegd voor reproduceerbare effectanalyse;
- de volledige lijn staat in een draft pull request en is nog niet definitief production-admitted.

## 26. Belangrijkste open punten

De belangrijkste nog te sluiten punten zijn:

1. exacte production control van `LWKM_makeHRU` binden;
2. het feitelijke R-script van HRU10242 toevoegen en tegen de documentatie controleren;
3. de exacte Flevoland-correctie reconstrueren, inclusief gekoppelde ontwaterings-/balanscomponenten;
4. vaststellen welk exact SVAT-bestand Piet voor HRU10242 heeft gebruikt;
5. vaststellen of dat bestand dezelfde Flevoland- en extremenstatus had als de later gebruikte SWAP-input;
6. formeel beleid voor verdachte/extreme SVATs vastleggen;
7. de exacte productie-inputs van `HRUlist2SWAP` binden;
8. het SWAP-inputpakket naar de gedistribueerde rekeneenheid binden;
9. het teruggekomen SWAP-resultaatpakket en de postprocessing binden;
10. de actuele SWAP-output- en balanscontrole aansluiten;
11. de vijfstappen-effectanalyse daadwerkelijk uitvoeren met echte cijfers;
12. de regionale analyse en visualisatie daarvan inrichten.

## 27. Hoofdbeeld

De belangrijkste verandering is niet dat alle inhoudelijke methoden nieuw worden.

Veel onderdelen bestonden al.

De verandering is dat we nu één beheersbare keten maken waarin per stap duidelijk is:

**welke bron → welke transformatie → welke output → welke QA → welke versie → welke volgende consument**

Daarmee kunnen toekomstige wijzigingen in:

- LHM;
- Flevoland-correcties;
- kennisregels;
- HRU-indeling;
- SWAP-mapping;
- rekentechniek;
- of downstream koppelingen

worden ingevoerd zonder opnieuw een ondoorzichtige keten van kopieën, handmatige correcties en moeilijk herleidbare tussenbestanden op te bouwen.

De huidige reconstructie is daarmee zowel:

- de verantwoording van de huidige LWKM 2.0-keten;
- als de basis voor een reproduceerbare, kritisch toetsbare en beter beheersbare volgende versie.
