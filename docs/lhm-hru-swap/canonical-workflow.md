# Canonical LHM → SVAT → HRU → SWAP workflow

Status: **DRAFT AUTHORITY**
Scope: vanaf geëxporteerde LHM-resultaten tot en met gecontroleerde SWAP-output.
Doel: een reproduceerbare, wijzigbare en auditeerbare werkstroom die onderzoekscycli ondersteunt zonder historische rommel te reproduceren.

## 1. LHM_EXPORT

### Doel

Op de NHI/LHM-server wordt niet de volledige modeluitvoer naar de LWKM-omgeving gekopieerd. In plaats daarvan wordt een gecontroleerd exportpakket gemaakt met alleen de downstream benodigde modeluitvoer, modelinvoer en statische gegevens.

### Minimale inhoud

Afhankelijk van de geldende LWKM-versie bevat het pakket ten minste:

- SVAT-identiteit en ruimtelijke ligging;
- oppervlak en gridreferentie;
- GHG en GLG;
- relevante waterbalansfluxen;
- MetaSWAP/MODFLOW-grootheden die downstream werkelijk worden gebruikt;
- landgebruik, bodem en overige benodigde classificaties;
- rastermaskers en aanvullende statische bestanden die nodig zijn om deze gegevens correct te interpreteren;
- bronperiode, LHM-versie, uitvoerende scripts en checksums.

### Regel

Een downstream stap mag geen impliciete afhankelijkheid hebben van willekeurige bestanden op de LHM-server. Alles wat nodig is om een run opnieuw te maken staat in het exportmanifest.

## 2. SVAT_BASE

### Doel

Alle benodigde geëxporteerde LHM-informatie en aanvullende basisinformatie worden geharmoniseerd tot één canonieke SVAT-dataset.

### Eigenschappen

Elke rij representeert één SVAT. De tabel bevat:

- stabiele SVAT-sleutel;
- bronwaarden;
- eenheden;
- periode/tijdsbetekenis;
- oppervlaktebasis;
- ruimtelijke kenmerken;
- landgebruik en bodem;
- hydrologische kenmerken en fluxen;
- provenance naar het producerende bronbestand.

Een correctie overschrijft nooit de oorspronkelijke waarde. Voor een te corrigeren variabele bestaan bijvoorbeeld afzonderlijke velden voor bronwaarde en gecorrigeerde waarde, aangevuld met correctietype, reden en configuratieversie.

## 3. SVAT_QUALIFIED

Deze stap bevat drie expliciet gescheiden beslissingen.

### 3.1 Domeinselectie

Bepaalt welke SVATs tot het LWKM-domein behoren.

Voorbeelden:
- landsgrens;
- landbouw en natuur;
- andere expliciete projectfilters.

De selectie wordt als flag opgeslagen. Niet-geselecteerde SVATs worden niet uit de brondata verwijderd.

### 3.2 Hydrologische correcties

Correcties worden alleen toegepast wanneer er een expliciet gedocumenteerde inhoudelijke reden is, bijvoorbeeld een bekende modelartefact-correctie.

Per correctie worden minimaal opgeslagen:

- target-SVAT;
- variabele;
- bronwaarde;
- gecorrigeerde waarde;
- correctieregel of algoritme;
- reden;
- configuratieversie;
- codecommit.

### 3.3 Kwalificatie / plausibiliteitsanalyse

Hydrologisch vreemde of onwaarschijnlijke SVATs worden via versieerbare regels gemarkeerd.

Een regel kan bijvoorbeeld afhangen van:
- kwel/wegzijging;
- runoff;
- infiltratie;
- GHG/Gt;
- landgebruik;
- een gebiedsuitzondering.

De uitkomst is niet alleen één veld "verdacht". Iedere regel houdt zijn eigen flag.

### Gebruikspolicy

Na diagnose wordt afzonderlijk vastgelegd hoe een gemarkeerde SVAT in volgende stappen wordt gebruikt:

- toegestaan voor HRU-clustering: ja/nee;
- toegestaan voor bepaling HRU-hydrologie: ja/nee;
- toegestaan voor specifieke SWAP-randvoorwaarde: ja/nee;
- donor/vervangingsbeleid: expliciet indien toegepast.

Een diagnose en een vervangingsactie zijn dus twee verschillende zaken.

## 4. HRU_DERIVATION

### Input

- SVAT_QUALIFIED;
- een versieerbare HRU-configuratie;
- noodzakelijke aanvullende ruimtelijke informatie.

### Output

- SVAT_HRU_MAP;
- HRU_SCHEMA;
- representatieve SVAT(s);
- HRU-raster;
- eventuele NRU-relatie;
- diagnostiek en kwaliteitsindicatoren;
- runmanifest.

### Regel

De HRU-procedure verandert SVAT_BASE of SVAT_QUALIFIED niet. Zij produceert uitsluitend nieuwe relaties en HRU-producten.

De huidige authority is HRU10242. De methodiek moet zodanig worden vastgelegd dat een toekomstige andere HRU-indeling naast HRU10242 kan bestaan zonder upstream data opnieuw te definiëren.

## 5. SWAP_INPUT_BUILD

### Doel

Uit SVAT-data, de SVAT-HRU-relatie, HRU-schema en een expliciete SWAP-mappingspecificatie wordt een SWAP-invoerpakket afgeleid.

### Per invoergrootheid moet bekend zijn

- bronvariabele;
- gebruikte SVAT-populatie;
- eventuele kwalificatiefilters;
- aggregatieregel;
- oppervlakteweging;
- gebruik van representatieve SVAT of groepsgemiddelde;
- eenheidsconversie;
- tekenconventie;
- tijdsbetekenis;
- fallbackregel.

Voorbeeldvragen die niet alleen in programmatuur verstopt mogen zitten:

- Welke bodemparameter komt van de representatieve SVAT?
- Welke meteorologische variabele wordt gemiddeld?
- Welke SVATs dragen bij aan drainageparameters?
- Wat gebeurt er wanneer alle leden van een HRU door een kwaliteitsregel worden uitgesloten?
- Hoe wordt kwel of een onderrandvoorwaarde afgeleid?

De mappingspecificatie is wetenschappelijke configuratie en hoort onder versiebeheer.

## 6. SWAP_RUN_QA

### Doel

SWAP wordt uitgevoerd met een volledig gemanifesteerd invoerpakket. De output wordt niet alleen op technische runstatus gecontroleerd, maar ook hydrologisch gekwalificeerd.

Minimaal:

- succesvolle runstatus;
- waterbalans;
- relevante toestandsvariabelen;
- bereik- en plausibiliteitscontroles;
- vergelijking met de LHM/SVAT-referentie op een identiek domein;
- afzonderlijke analyse van HRU-representatie-effect en SWAP-modeleffect waar dat mogelijk is.

## 7. HANDOFF

Na kwalificatie wordt een expliciet SWAP-handoffpakket gemaakt voor de volgende LWKM-stap, bijvoorbeeld ANIMO.

De verwerking ná deze overdracht valt buiten deze workflow.

## 8. Onderzoekscycli

De workflow ondersteunt iteratie zonder bestaande resultaten te overschrijven.

Voorbeeld:

1. SWAP_QA ontdekt onwaarschijnlijk hoge drainage in een aantal HRUs.
2. Analyse herleidt dit tot enkele SVATs of een mappingregel.
3. Er wordt een wijzigingsvoorstel gemaakt.
4. De relevante configuratie krijgt een nieuwe versie.
5. Alleen de benodigde downstream stappen worden opnieuw uitgevoerd.
6. Oude en nieuwe run worden objectief met elkaar vergeleken.
7. Na acceptatie wordt de nieuwe configuratie de canonical baseline.

De terugkoppeling gaat dus via **configuratie en versiebeheer**, niet via handmatige aanpassing van eindbestanden.

## 9. Runidentiteit

Iedere reproduceerbare run krijgt één unieke run-id, bijvoorbeeld:

LWKM20-LHM433-HRU10242-SWAP5-20260924-01

Een run-id verwijst altijd naar:

- inputmanifest;
- configuratieversies;
- codecommits;
- uitvoerbestanden;
- QA-resultaten;
- eventuele afwijkingen of uitzonderingen.

## 10. Basisregel voor wijzigingen

Geen enkel getal in een canonical product mag veranderen zonder dat minimaal één van deze vier zaken zichtbaar verandert:

1. inputversie;
2. configuratie;
3. codecommit;
4. expliciet vastgelegde handmatige correctie.

Daarmee wordt een verandering altijd herleidbaar.
