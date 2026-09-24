# Notitie: workflow van LHM naar SWAP via de HRU-systematiek

**Project:** LWKM 2.0  
**Status:** concept werknotitie, 24 september 2026  
**Doel:** inzichtelijk maken hoe LHM-resultaten gecontroleerd worden omgezet naar SVAT-informatie, HRU's en uiteindelijk SWAP-invoer, en hoe wijzigingen en kwaliteitscontroles daarin voortaan reproduceerbaar worden vastgelegd.

## 1. Aanleiding

De huidige LWKM-werkwijze is in de loop van meerdere jaren stapsgewijs opgebouwd. Daarbij zijn analyses, correcties, selecties, HRU-afleiding en SWAP-invoer op verschillende locaties en in verschillende scripts terechtgekomen. Dat was logisch tijdens de ontwikkeling, maar maakt het nu lastig om precies te reconstrueren:

- welke LHM-resultaten als basis zijn gebruikt;
- welke SVATs zijn geselecteerd of gecorrigeerd;
- waarom bepaalde hydrologisch vreemde SVATs wel of niet worden gebruikt;
- hoe de HRU-indeling uit de SVATs is afgeleid;
- hoe HRU-eigenschappen worden vertaald naar SWAP-invoer;
- wat het hydrologische effect is van iedere stap.

De huidige reconstructie heeft inmiddels voldoende informatie opgeleverd om niet alleen de bestaande keten beter te begrijpen, maar ook een strakkere werkwijze voor volgende LWKM-versies vast te leggen.

De nieuwe aanpak maakt daarom onderscheid tussen:

1. **reconstructie van de huidige LWKM 2.0-keten**, voor verantwoording van bestaande resultaten;
2. **een canonical workflow**, die voorschrijft hoe volgende runs reproduceerbaar en onder versiebeheer worden uitgevoerd.

## 2. Afbakening

De volledige LHM-berekening valt buiten deze workflow. Het startpunt is het eindproduct van een afgeronde LHM-run op de NHI/LHM-server.

Het eindpunt is een gecontroleerd SWAP-uitvoerpakket dat kan worden overgedragen aan de volgende LWKM-stap. De verdere verwerking richting ANIMO valt buiten deze werkstroom.

De hoofdroute is:

```text
LHM-run
   │
   │  gecontroleerde export
   ▼
LHM_EXPORT
   │
   │  verzamelen en harmoniseren
   ▼
SVAT_BASE
   │
   │  selectie + correcties + kwaliteitsregels
   ▼
SVAT_QUALIFIED
   │
   │  HRU-afleiding
   ▼
SVAT_HRU_MAP + HRU_SCHEMA
   │
   │  expliciete vertaling naar SWAP
   ▼
SWAP_INPUT
   │
   ▼
SWAP
   │
   ▼
SWAP_OUTPUT + QA
   │
   └──► overdracht naar ANIMO
```

De datastroom is lineair, maar de ontwikkeling is dat niet. Een afwijkend SWAP-resultaat kan aanleiding zijn om een selectieregel, correctie, HRU-instelling of SWAP-mapping opnieuw te onderzoeken. Zo'n terugkoppeling leidt voortaan tot een nieuwe versie van configuratie en resultaten, niet tot een handmatige wijziging van bestaande eindbestanden.

## 3. Stap 1: gecontroleerde export uit LHM

Op de LHM-server is zeer veel modeluitvoer beschikbaar. Het is niet wenselijk en ook niet nodig om die volledige uitvoer naar de LWKM-omgeving over te zetten.

Daarom wordt een formeel **LHM_EXPORT-pakket** gedefinieerd. Daarin worden alleen gegevens opgenomen die downstream aantoonbaar nodig zijn, bijvoorbeeld:

- SVAT-identiteit en ruimtelijke ligging;
- GHG en GLG;
- relevante waterbalanscomponenten;
- kwel en wegzijging;
- drainage, runoff, infiltratie en beregening;
- relevante MetaSWAP- en MODFLOW-grootheden;
- tijdsafhankelijke MODFLOW-informatie die nodig is voor SWAP-randvoorwaarden;
- noodzakelijke statische gegevens en classificaties.

Bij ieder exportproduct worden voortaan versie, periode, eenheid, oppervlaktebasis, bronbestand, producerend script en checksum vastgelegd.

Hiermee wordt de grens helder: **LHM is upstream authority; LWKM begint bij een gecontroleerde en reproduceerbare export.**

## 4. Stap 2: één canonieke SVAT-dataset

Binnen de LWKM-omgeving worden LHM-uitvoer, LHM-invoer en aanvullende ruimtelijke gegevens bij elkaar gebracht in één SVAT-dataset.

De huidige Fortran-route via `LWKM_makeHRU` laat zien welke informatie hiervoor in de praktijk al wordt gecombineerd. De huidige tabel bevat onder meer:

- SVAT-id, coördinaten en oppervlak;
- GHG en GLG;
- neerslag en verdamping;
- runoff;
- afvoer en aanvoer per systeem;
- kwel en wegzijging;
- drainage en beregening;
- landgebruik en bodemindelingen;
- hydrologische klassevariabelen;
- kwaliteits-/selectievelden;
- aanvullende MetaSWAP- en MODFLOW-grootheden.

Voor de toekomstige werkwijze wordt deze tabel conceptueel opgesplitst in:

**SVAT_BASE**  
De oorspronkelijke en afgeleide broninformatie. Waarden worden hier niet destructief overschreven.

**SVAT_QUALIFIED**  
De beslislaag waarin selectie, correcties, kwaliteitsflags en downstream gebruiksregels worden vastgelegd.

Dit onderscheid is nodig om later altijd te kunnen achterhalen welke waarde uit LHM kwam en welke waarde of selectie het gevolg is van een LWKM-besluit.

## 5. Stap 3: selectie, correctie en kwalificatie van SVATs

Deze stap bevat drie verschillende typen bewerking die voortaan expliciet uit elkaar worden gehouden.

### 5.1 Selectie van het LWKM-domein

Niet iedere LHM-SVAT wordt in LWKM gebruikt. De huidige dataset bevat hiervoor onder andere het veld `isLWKM`. Dit is een sterke kandidaat voor de selectie landbouw + natuur.

Het effect van deze stap is een **selectie-effect**: het aantal SVATs en het vertegenwoordigde oppervlak veranderen. De hydrologie van een behouden SVAT hoort door deze selectie zelf niet te veranderen.

### 5.2 Inhoudelijke correcties

Wanneer een bekend modelartefact een hydrologische grootheid fout of ongeschikt maakt, kan een correctie nodig zijn. De huidige werkstroom bevat bijvoorbeeld een correctie rond Flevoland/kwel.

Een correctie wordt voortaan niet meer alleen als een vervangen waarde bewaard. Per wijziging worden ook vastgelegd:

- oorspronkelijke waarde;
- gecorrigeerde waarde;
- correctieregel;
- ruimtelijk toepassingsgebied;
- reden;
- versie van de configuratie.

De precieze authority voor de huidige Flevoland-correctie wordt nog gereconstrueerd.

### 5.3 Hydrologische plausibiliteitscontrole

Een deel van de LHM-uitvoer bevat waarden die aanleiding geven tot nader onderzoek, bijvoorbeeld zeer hoge kwel, sterke wegzijging, extreme runoff of combinaties van grondwaterstand en flux die niet plausibel lijken.

In de huidige scripts zijn hiervoor al verschillende selectieregels aanwezig. In het blok “afspraken okt-25” staan bijvoorbeeld criteria voor:

- hoge subinfiltratie;
- hoge runoff, met verschillende grenzen voor landbouw en niet-landbouw;
- sterke wegzijging;
- sterke kwel;
- kwel bij een droge grondwatertrap;
- GHG boven maaiveld bij landbouw.

Een belangrijke wijziging in de nieuwe werkwijze is dat **signaleren en handelen twee aparte stappen worden**.

Een SVAT kan dus worden gemarkeerd als verdacht zonder dat hij automatisch wordt vervangen. Vervolgens wordt expliciet bepaald of die SVAT:

- mag worden gebruikt bij HRU-clustering;
- mag bijdragen aan hydrologische HRU-randvoorwaarden;
- voor een specifieke SWAP-invoergrootheid mag worden gebruikt;
- via een donor of andere methode moet worden vervangen.

Dat maakt veranderende inzichten beheersbaar. Een nieuwe uitzondering of aangepaste drempel wordt een nieuwe configuratieversie en kan objectief tegen de vorige versie worden doorgerekend.

## 6. Stap 4: afleiden van HRU's

Na de SVAT-kwalificatie volgt een zelfstandige HRU-procedure.

De actuele authority voor deze werkstroom is **HRU10242**. Oudere HRU-versies worden niet verder uitgewerkt, behalve wanneer ze nodig zijn om de provenance van de huidige lijn te begrijpen.

De huidige HRU-methode combineert:

- een hiërarchie van bodem-, landgebruik- en hydrologische kenmerken;
- clustering op GHG en netto kwel;
- minimale groepsgrootte;
- MAE-/spreidingscontroles;
- donor-matching voor SVATs die niet rechtstreeks in een cluster passen;
- selectie van een representatieve SVAT per HRU.

Het resultaat bestaat niet uit één bestand, maar uit meerdere expliciete producten:

- **SVAT_HRU_MAP:** welke SVAT hoort bij welke HRU;
- **HRU_SCHEMA:** eigenschappen van iedere HRU;
- representatieve SVAT(s);
- HRU-raster;
- kwaliteitsinformatie, zoals purity en afwijkingen in GHG/netto kwel.

Een belangrijk uitgangspunt is dat de HRU-procedure de SVAT-dataset niet wijzigt. Zij voegt een nieuwe representatielaag toe.

## 7. Stap 5: van HRU naar SWAP-invoer

De overgang van HRU naar SWAP is een afzonderlijke modelleringstap. Hiervoor wordt de huidige `HRUlist2SWAP`-route gereconstrueerd.

Uit de broncode blijkt dat verschillende SWAP-invoergrootheden op verschillende manieren worden afgeleid. Voorbeelden zijn:

- keuze van bodem en landgebruik;
- gebruik van de representatieve SVAT;
- gemiddelde of meerderheidswaarden binnen een HRU;
- selectie van SVATs voor bepaalde hydrologische randvoorwaarden;
- afleiding van drainagekenmerken;
- berekening van de onderrand;
- oppervlaktegewogen meteorologische invoer.

Deze regels worden voortaan vastgelegd in een aparte **SWAP_MAPPING**. Per SWAP-veld moet daarin duidelijk zijn:

- uit welk bronproduct het komt;
- welke SVATs worden gebruikt;
- welke aggregatieregel geldt;
- of een representatieve SVAT wordt gebruikt;
- welke eenheidsconversie plaatsvindt;
- welke fallback geldt.

Hierdoor kan een wijziging in één mappingregel later gericht worden onderzocht zonder de hele keten opnieuw te interpreteren.

## 8. Stap 6: SWAP-run en hydrologische QA

Na het genereren van SWAP-invoer worden alle HRU's doorgerekend.

De controle eindigt niet bij “SWAP heeft succesvol gedraaid”. De uitvoer wordt opnieuw hydrologisch onderzocht:

- sluiten de waterbalansen;
- zijn toestandsvariabelen plausibel;
- zijn er HRU's met sterk afwijkend gedrag;
- is een afwijking afkomstig uit de oorspronkelijke LHM-hydrologie;
- komt hij door de HRU-representatie;
- komt hij door de SWAP-inputmapping;
- of ontstaat hij pas in de SWAP-berekening?

Daarmee kan een probleem gericht worden teruggebracht naar de stap waar het ontstaat.

De onderzoekslus wordt formeel:

**OBSERVE → LOCALIZE → PROPOSE → CANDIDATE RUN → COMPARE → ACCEPT/REJECT → PERSIST**

Een nieuwe kandidaat overschrijft een oude run niet.

## 9. Effecten per stap kwantificeren

De projectleider heeft gevraagd om de hydrologisch relevante veranderingen tussen de verschillende stadia te kunnen kwantificeren.

Daarvoor wordt de bestaande indeling als volgt geïnterpreteerd:

| Stap | Te rapporteren effect |
|---|---|
| LHM4.3 | uitgangstoestand van de relevante LHM-hydrologie |
| LHM4.3 lbn | effect van selectie van het LWKM-domein |
| LHM4.3 cor | effect van inhoudelijke correcties, op exact dezelfde SVATs |
| LHM4.3 rep | effect van kwaliteits-/vervangingsbeleid voor vreemde hydrologie |
| LWKM SVATs | verschil tussen LHM en 1:1 SWAP voor de gekozen representatieve SVATs |
| LWKM HRU's | effect van HRU-aggregatie en representatie |
| LWKM rep | effect van eventuele vervanging/correctie op HRU-niveau |

Per overgang worden waar relevant minimaal gerapporteerd:

- aantal SVATs/HRU's;
- oppervlak;
- aantal en oppervlak gewijzigde eenheden;
- gebiedsgewogen gemiddelde vóór en na;
- gemiddelde absolute afwijking;
- RMSE;
- extremen/percentielen;
- ruimtelijke ligging van de verschillen.

Daarvoor is inmiddels een eerste reproduceerbare QA-tool in de LWKM-repository ingericht.

## 10. Versiebeheer en reproduceerbaarheid

De workflow wordt ondergebracht in de GitHub-repository:

`abhedwig-cell/LWKM`

Voor iedere kandidaat- of productierun wordt een manifest gebruikt waarin minimaal staan:

- LHM-bronversie;
- inputbestanden en checksums;
- codecommit;
- configuratieversies;
- HRU-versie;
- SWAP-versie;
- outputlocaties;
- QA-status.

De basisregel wordt:

> Geen getal in een canonical product verandert zonder dat zichtbaar is welke input, configuratie, code of expliciete correctie is gewijzigd.

Onderzoek blijft daardoor mogelijk, maar iedere nieuwe keuze kan worden teruggevonden en tegen de vorige versie worden vergeleken.

## 11. Stand van zaken

De afgelopen reconstructie heeft inmiddels het volgende opgeleverd:

- de globale LHM → SVAT → HRU → SWAP-keten is gereconstrueerd;
- de NHI/LHM-nabewerkingsscripts zijn gedeeltelijk in beeld;
- de huidige 75-koloms SVAT-interface uit `LWKM_makeHRU v0.20` is gedocumenteerd;
- de actuele HRU10242-lijn is als authority gekozen;
- de HRU-clustering is technisch gedocumenteerd;
- de huidige `HRUlist2SWAP v0.38`-mapping is grotendeels veld voor veld gereconstrueerd;
- de belangrijkste kwalificatieregels zijn uit de scripts gehaald en als versieerbare configuratie vastgelegd;
- een runmanifest, wijzigingsprocedure en effect-accountingstructuur zijn opgezet;
- een eerste QA-tool is toegevoegd om de hydrologische verschillen per stap reproduceerbaar te berekenen;
- de volledige lijn staat in een draft pull request en wordt nog niet als definitieve productieauthority beschouwd.

De voornaamste open punten zijn:

1. exacte production control van `LWKM_makeHRU` binden;
2. het feitelijke R-script van HRU10242 toevoegen en tegen de documentatie controleren;
3. de Flevoland-correctie exact reconstrueren;
4. de overgang van signalering naar uitsluiten/vervangen formeel vastleggen;
5. de actuele SWAP-output- en balanscontrole aan de workflow koppelen;
6. de eerste volledige effecttabel voor de projectleider uitvoeren.

## 12. Hoofdbeeld

De belangrijkste verandering is niet dat de inhoudelijke methode volledig nieuw wordt. Veel onderdelen bestaan al.

De verandering is dat iedere stap nu een **duidelijke productgrens, configuratie en provenance** krijgt. Daardoor kan een nieuwe LHM-versie, een nieuwe hydrologische kwaliteitsregel, een andere HRU-indeling of een aangepaste SWAP-vertaling later worden ingevoerd zonder opnieuw een ondoorzichtige keten op te bouwen.

De huidige reconstructie vormt daarmee zowel de verantwoording van LWKM 2.0 als de basis voor een beter beheersbare volgende versie.
