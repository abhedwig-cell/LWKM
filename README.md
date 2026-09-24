# LWKM

Werkrepository voor de verdere ontwikkeling en kwalificatie van het Landelijk Waterkwaliteitsmodel (LWKM).

## Projectbaseline

Deze repository is gestart op basis van eerder werk rond SWAP5, ANIMO5 en WOFOST. De repository is niet bedoeld als kopie van die modelrepositories. Zij wordt de plaats voor de ketenarchitectuur, koppelcontracten, integratietests en kwalificatie-evidence van LWKM.

### Doelbeeld

Het beoogde systeem bestaat uit zelfstandige modellen met expliciet proces- en state-ownership:

- **SWAP5**: hydrologie en bodemwater, inclusief de relevante waterfluxen en hydrologische toestand.
- **ANIMO5**: bodemnutriënten en waterkwaliteit.
- **WOFOST 8.1**: gewasgroei, gewasontwikkeling en de relevante gewas-N-respons.
- **LWKM**: orkestratie en expliciete uitwisseling tussen deze modellen. LWKM neemt geen modelinterne fysica over die bij een componentmodel hoort.

De centrale nieuwe ontwikkellijn is een online koppeling **SWAP5 ⇄ ANIMO5 ⇄ WOFOST 8.1**, in eerste instantie op dagbasis. Een fijnere koppeltijdstap is niet bij voorbaat gewenst en moet alleen worden ingevoerd als procesanalyse aantoont dat die nodig is.

### Architectuurprincipes

De bestaande SWAP5- en ANIMO5-modernisering levert de methodologische basis:

1. expliciete state, parameters en forcing;
2. duidelijk ownership van toestand, fluxen en processen;
3. transactionele uitvoering met trial, assess, commit/rollback waar koppeling of numeriek beleid dat vereist;
4. expliciete tijdstap- en retrysemantiek;
5. massabalans als harde kwalificatie-eis;
6. typed exchange contracts in plaats van impliciete bestandssemantiek;
7. deterministic replay en reproduceerbare provenance;
8. theory → documentation → code → tests → evidence traceability;
9. verschillen met legacy gedrag worden geclassificeerd en niet stilzwijgend weggewerkt;
10. componentmodellen blijven waar mogelijk zelfstandig uitvoerbaar.

Generieke runtime-mechanismen mogen tussen modellen worden hergebruikt. Wetenschappelijke modelsemantiek blijft modelspecifiek.

### Bestaande evidence die als upstream geldt

#### SWAP5

SWAP5 heeft al werk opgeleverd rond transactionele state, checkpoint/restore, solver-policy-separatie, restart, MultiSWAP, WOFOST 8.1, groundwater coupling en systematische qualification. Dit is upstream evidence en wordt niet opnieuw als LWKM-resultaat geclaimd.

De WOFOST 8.1-lijn heeft een SWAP4.3.1 → SWAP5 migratie en oracle-vergelijking opgeleverd. De exacte aangepaste SWAP4.3.1 donorartifact is in die provenance-lijn nog als ontbrekend gemarkeerd. Dat provenanceprobleem mag in LWKM niet worden weggepoetst.

#### ANIMO5

ANIMO5 wordt afzonderlijk gemoderniseerd vanuit een frozen legacy reference naar een corrected reference en vervolgens een nieuwe architectuur. LWKM wacht niet met architectuurdenken tot ANIMO5 volledig af is, maar mag onvoltooide ANIMO5-evidence niet als gekwalificeerde productie-interface behandelen.

Eerder werk heeft al een modelneutrale runtime met SWAP- en ANIMO-clients en een typed hydrology exchange seam onderzocht. Dit vormt een bruikbaar vertrekpunt, geen automatisch production contract.

### Centrale koppelvraag

De belangrijkste nog open wetenschappelijke en softwarematige vraag is niet alleen hoe data worden doorgegeven, maar **welk model eigenaar is van welk proces en op welk moment een uitgewisselde grootheid geldig wordt**.

Voor de SWAP5–ANIMO5–WOFOST 8.1 driehoek moeten ten minste de volgende zaken prospectief worden vastgelegd:

- definitie van plantbeschikbare N;
- vertaling van ANIMO-toestand/fluxen naar een WOFOST N-limitatie of N-opnamevraag;
- ownership van feitelijke N-opname;
- wortelverdeling en relevante gewastoestand terug naar ANIMO;
- effect van N-limitatie op WOFOST-groei;
- terugwerking van veranderde groei, transpiratievraag en wortelontwikkeling naar SWAP;
- daggrenssemantiek: welke toestand is committed, welke forcing geldt voor de volgende stap en in welke volgorde worden modellen aangeroepen;
- massa-accounting voor water, N en andere relevante stoffen over modelgrenzen;
- rollback/retry-semantiek wanneer een componentstap niet wordt geaccepteerd.

### Qualification

LWKM gebruikt dezelfde discipline als de moderniseringsprojecten, maar bouwt eigen ketenevidence op:

**RECONCILE → AUTHORITY BINDING → PREREGISTER → IMPLEMENT → QUALIFY → ADMIT → CLOSE**

Minimale testlagen:

- component-interface tests;
- contract tests voor units, tekenconventies, tijdsreferentie en state validity;
- conservation/mass-balance tests;
- deterministic replay;
- controlled oracle cases;
- coupled regression cases;
- failure/retry/rollback tests;
- end-to-end ketencases;
- provenance en reproduceerbaarheid.

### Eerste werkstromen

**LWKM-ARCH**  
Formele ketenarchitectuur en ownership matrix voor SWAP5, ANIMO5 en WOFOST 8.1.

**LWKM-NCOUPLE**  
Prospectieve definitie en falsificatie van de dagelijkse N-koppeling ANIMO5 ⇄ WOFOST 8.1, inclusief feedback naar SWAP5.

**LWKM-HYDRO-ANIMO**  
Formaliseren en kwalificeren van het SWAP5 → ANIMO5 hydrology exchange contract. Eerder seam-werk wordt gereconcilieerd, niet blind overgenomen.

**LWKM-RUNTIME**  
Bepalen welk deel van de transactionele/modelneutrale runtime daadwerkelijk gedeeld kan worden zonder modelspecifieke semantiek te vermengen.

**LWKM-E2E**  
Kleine gecontroleerde end-to-end testbank voor SWAP5 + ANIMO5 + WOFOST 8.1.

### Expliciet buiten deze repository

- algemene SWAP5 solverontwikkeling;
- algemene ANIMO5 migratie;
- algemene WOFOST-ontwikkeling;
- duplicatie van componentmodeltests die geen ketencontract testen.

Die werkzaamheden blijven in hun eigen repositories en worden hier als gepinde upstream dependencies behandeld.

## Eerstvolgende stap

De eerste inhoudelijke werkunit is **LWKM-ARCH01**: reconcilieer de bestaande koppelideeën en prototypes tot één prospectieve ownership- en timingmatrix. Pas daarna wordt de N-koppeling als executable contract vastgelegd.
