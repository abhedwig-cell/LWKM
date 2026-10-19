# Uitvoerings- en kwalificatierapport

Actuele Work C2-aanvulling: [definitieve drainageregels en uitvoering](WORK_C2_20261019.md). Oudere resultaten hieronder blijven historische evidence.

Actuele aanvulling: [Work C, uitvoering en kwalificatie](WORK_C_20261019.md). Onderstaande oorspronkelijke sessieresultaten blijven als historische context behouden.

Bronbaseline: 4e6c5803b8d9f996c3331078ac72c6ece6db4a97. De exacte geteste codebytes staan in ../evidence/2026-10-19/code-file-hashes.json. Status: gedeeltelijk operationeel, geen integrale production admission.

| Proef | Werkelijk resultaat | Begrenzing |
|---|---|---|
| Lokale softwaretests | Zie tests.log, alle tests geslaagd | Unit- en contracttests zijn geen fysische validatie |
| Q4 bytecontrole | 705/705 payloadleden correct | Geen automatische semantische admission |
| Workbook | 22 werkbladen, 337.098 formulecaches | Bronwerkboek blijft authority |
| Contexten | 10.242, nul unresolved joins | Upstream lineage niet volledig admitted |
| Membership | 427.656 leden, 10.242 HRU's/representanten | Bestaande partitionering gereconstrueerd |
| SWP-populatie | 10.242, nul generatiefouten | Geen 10.242 complete pakketten |
| Incrementele herbouw | 10.242 ongewijzigde SWP's hergebruikt | Zelfde bron, code en profiel |
| SWP-oraclevergelijking | 49 verschillenlijsten behouden | Nul historische-equivalentie-admissions |
| Ongewijzigde historische uitvoering | 0/49 succesvolle volledige runs | BBC-diagnoseformat en executable niet compatibel |
| Modern interfaceonderzoek 1971 | 45/49 succesvol | Historische MET/DRA en eerste BBC-diagnosekolom |
| Vier mislukte interfacegevallen | 7871, 7909, 7910, 7911 | SWETR=1 vereist actieve crop factors |
| Nieuwe DRA, 49 HRU's in 1971 | 2 source failures, 19 protected/interface failures op overige 47 | Niet geschikt voor algemene admission |
| Nieuwe DRA voorbeeld 7876 | Volledige 1971-run succesvol | MET en BBC blijven onderzoeksinvoer |
| W11 voorbeeldpakket | 6 assets atomair samengesteld en gehasht | PACKAGE_CANDIDATE_NOT_ADMITTED |
| W08-GW-L1 | Algoritme en conserveringstests geslaagd | Dagelijkse oorspronkelijke bronsemantiek niet production-bound |

## Betekenis van drainagefalen

HRU's 7870 en 7929 hebben een ontbrekende H1-infiltratiefactor op positieve-conductantieleden. Het eerdere nulbeleid geldt voor P/S/T en mag niet zonder bronbesluit op H1 worden toegepast. Het raster is teruggevonden; de ontbrekende semantische waarde blijft een echte bronblokkade.

Voor 19 van de overige 47 gevallen weigert de beschermde kandidaat de compressie of interface. Een aangetroffen voorbeeld is H1 INFRES=342317.93 dagen bij HRU 7866, boven de SWAP-grens van 100000. Een stille afkapping zou de conductantie veranderen en is niet toegelaten.

De oorspronkelijke renderer schreef DRARES, INFRES en L als gehele tokens. De echte SWAP-parser weigert die voor reële variabelen. De moderne serializer schrijft nu expliciet reële tokens met behoud van numerieke precisie. Daarmee is het voorbeeld 7876 daadwerkelijk uitgevoerd.

## Reproduceerbare evidence

De CSV population-swp-identities.csv bevat alle SWP-identiteiten. runtime-49.json bevat de input- en outputhashes per geval. execution-results.zip bewaart dagelijkse resultaten en logs van de 49 interfaceproeven plus één volledige invoerset. modern-dra-example.zip bewaart de nieuwe DRA-demonstratie. q4-reverification.json en source-members.json bewaren de afzonderlijke bronidentiteiten.

De 45 succesvolle technische proeven laten over 1971 ongeveer 389 tot 579 mm totale verdamping zien. Er is geen onafhankelijke validatie of landelijke weging. De maximale absolute dagelijkse BALDEV is circa 0,088 mm en de eindjaarsboekhouding moet verder worden beoordeeld.

## Open admissioncriteria

Geen volledige moderne productie-uitvoering is toegelaten. Nodig zijn complete geconsumeerde dagelijkse bronnen, gekwalificeerde package-tekens en tijdsaggregatie, een onderbouwde W08-route, oplossing van de drainage-uitzonderingen en vier crop-factorcombinaties, complete assets, fysische resultatencontrole en een volledige recursieve bronregistratie. De historische produceridentiteit blijft een afzonderlijke equivalentiebeperking.

De volledige 10.242-HRU-drainagesensitiviteitsrun voor 1970-2021 is gestart en daarna gestopt toen de referentieset aantoonbaar faalde op vereiste bron- en interfacegates. De grote run levert geen afgeronde populatiekwalificatie op. Het stoppunt en de rekentijd staan in dra-full-attempt.json.
