# Qualification and change control

Status: **DRAFT AUTHORITY**

De LWKM-werkstroom moet onderzoek en correctie faciliteren zonder bestaande runs onzichtbaar te muteren.

## 1. Statussen

Voor code, configuratie en workflows gebruiken we drie statussen:

- **EXPERIMENTAL**: vrije onderzoeksvariant, niet geschikt als projectauthority.
- **CANDIDATE**: inhoudelijk onderbouwde variant die tegen de canonical baseline wordt vergeleken.
- **CANONICAL**: geaccepteerde baseline voor nieuwe productieruns.

## 2. Geen wijziging zonder vergelijking

Een wijziging die hydrologische resultaten kan beïnvloeden krijgt minimaal:

- wijzigings-id;
- aanleiding;
- getroffen workflowstap;
- oude configuratie/code;
- nieuwe configuratie/code;
- verwachte effectrichting;
- vergelijking oud versus nieuw;
- besluit en motivatie.

## 3. Impactgebied

Elke wijziging declareert waar herberekening nodig is.

Voorbeelden:

- wijziging LHM-export: herbereken alle downstream producten;
- wijziging SVAT-correctie: herbereken SVAT_QUALIFIED en downstream;
- wijziging HRU-configuratie: behoud SVAT-producten, herbereken HRU en downstream;
- wijziging SWAP-mapping: behoud HRU-producten, herbereken SWAP_INPUT en downstream;
- wijziging alleen QA-visualisatie: productdata hoeven niet opnieuw te worden berekend.

## 4. Runmanifest

Iedere canonical of candidate run heeft een manifest met:

- run_id;
- parent_run_id indien relevant;
- LHM-bronversie;
- inputbestanden + checksums;
- codecommit(s);
- configuratieversies;
- HRU-versie;
- SWAP-versie;
- datum;
- uitvoerlocaties;
- QA-status;
- bekende afwijkingen.

## 5. Onderzoekslus

De formele lus bij een probleem is:

OBSERVE → LOCALIZE → PROPOSE → RUN CANDIDATE → COMPARE → ACCEPT/REJECT → PERSIST

Voorbeeld:

1. een SWAP-run toont onwaarschijnlijk hoge grondwateraanvoer;
2. analyse koppelt dit aan een subset SVATs;
3. een nieuwe kwalificatieregel of mappingwijziging wordt voorgesteld;
4. kandidaat-run wordt gemaakt;
5. alleen relevante verschillen worden vergeleken;
6. besluit wordt vastgelegd;
7. bij acceptatie wordt de kandidaat de nieuwe canonical baseline.

## 6. Wat nooit mag gebeuren

- handmatig een canonical CSV aanpassen zonder wijzigingsrecord;
- een drempel in code wijzigen zonder configuratieversie;
- bestanden overschrijven zodat oude runs niet meer reproduceerbaar zijn;
- een mislukt experiment als nieuwe baseline gebruiken omdat het bestand toevallig recenter is;
- een downstream probleem terugrepareren in een eindbestand zonder de upstream oorzaak te registreren;
- historische onderzoeksvarianten opnemen in canonical documentatie alsof ze nog actief zijn.

## 7. Baselinevergelijking

Een kandidaat wordt niet alleen beoordeeld op "ziet er beter uit". Minimaal worden waar relevant vergeleken:

- aantal en oppervlak geselecteerde SVATs;
- aantallen per qualification rule;
- hydrologische verdelingen;
- waterbalanstermen;
- HRU-aantal en veranderde SVAT→HRU-toewijzingen;
- representatieve SVATs;
- SWAP run failures;
- SWAP waterbalans en relevante toestanden;
- afwijking ten opzichte van de upstream hydrologische referentie.

## 8. Canonical admission

Een candidate mag CANONICAL worden wanneer:

- input en configuratie volledig zijn gemanifesteerd;
- code reproduceerbaar is;
- de wijziging inhoudelijk is beschreven;
- regressies zijn beoordeeld;
- relevante QA is geslaagd;
- bekende beperkingen expliciet zijn vastgelegd.

De canonical status betekent niet dat de methode definitief is. Zij betekent alleen dat dit de geautoriseerde basis is waartegen de volgende wijziging wordt beoordeeld.
