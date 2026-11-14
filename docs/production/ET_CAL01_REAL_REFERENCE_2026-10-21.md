# ET-CAL01: eerste echte pilotreferentie ontvangen en onderzocht

21 oktober 2026. Status: `REAL_PILOT_RECEIVED_NOT_CALIBRATION_READY`. De ontbrekende referentie is voor de 21 vooraf geselecteerde HRU's ontvangen. De ontvangst en referentieanalyse zijn uitgevoerd; nul nieuwe SWAP-runs en nul feitelijke kalibraties. Er is geen landelijke kalibratie of productie-admission.

## Ontvangst, bronbinding en reikwijdte

`HRU21_export_20261021_085909_314.zip` bevat 1.980 aaneengesloten kalenderdecades van 1 januari 1970 tot en met 31 december 2024. De 21 HRU's leveren samen 41.580 regels en 1.155 volledige HRU-jaren. Alle negen oorspronkelijke ET/vraag/gift-termen zijn volledig gedekt; er zijn nul onvolledige HRU-decades. De aangeleverde selectie is gelijk aan de vooraf vastgelegde pilot. Alleen de CSV-regelafbrekingen verschillen door de Windows-checkout; beide bestandshashes worden behouden en de velden zijn identiek na normalisatie van uitsluitend de regelafbrekingen.

Alle 7.927 assethashes, het gesloten bestandsmanifest en de voltooiingshash zijn gecontroleerd. De gezamenlijke CSV is veld voor veld gelijk aan de 1.980 afzonderlijke selectietabellen. Per decade zijn de originele marker, QC-hash, geselecteerde uitvoerhash en relatie met de geregistreerde volledige bron-CSV gecontroleerd. De bestaande `tools.receive_et_reference` heeft de volledige reeks vervolgens ontvangen en opnieuw geverifieerd als `real_unreviewed`. Dat is een onveranderlijke transportontvangst, geen fysische toelating.

De oorspronkelijke landelijke IDF's en volledige 10.242-HRU-CSV's zijn niet lokaal ontvangen of opnieuw gehasht. De hashes daarvan worden uit de originele producentmarkers behouden. Deze grens staat expliciet in `reception.json`. De oorspronkelijke upload blijft beschikbaar via de vastgelegde Library-identiteit en SHA-256; Git bewaart ook de exacte gezamenlijke CSV-bytes, gecomprimeerd zonder teken- of getalwijziging, en de oorspronkelijke gecomprimeerde hashmanifesten.

Een aanvullende ruimtelijke controle was wel mogelijk. De oorspronkelijke `area_svat.inp` en `svat_hru.csv` zijn uit het eerder gemaakte producentpakket teruggevonden. Hun hashes zijn exact gelijk aan de nieuwe `source_run_identity.txt`. Alle 427.656 SVAT-HRU-koppelingen zijn identiek aan de gekwalificeerde Work B-membership. Reconstructie met de oorspronkelijke SVAT-oppervlakken reproduceert voor alle 10.242 HRU's zowel het aantal leden als het oppervlak exact. Er is geen HRU, representant, donor of bodem opnieuw gekozen.

Het bronoppervlak is 25.514.516.032 m². De geselecteerde HRU's vertegenwoordigen samen 51.480.392 m², ongeveer 0,2018% daarvan. Dat is de geselecteerde support, geen bewijs van nationale representativiteit. De zeven profielen en 21 BOFEK-labels blijven een ontworpen onderzoeksselectie.

## Tekenconventie en numerieke ET-controles

De ruwe ET- en vraagtermen en BDGETACT zijn negatief of nul; PSGW en PSSW zijn positief of nul. Voor deze diagnose is expliciet de hypothese gebruikt dat vermenigvuldiging met -1 voor de zeven ET/vraag/BDGETACT-termen en +1 voor de twee giften positieve verliezen en giften geeft. Dit is geen afleiding van tekens uit een meerderheid van de waarden en geen automatische `SEMANTICS_REVIEWED`-verklaring. De gebruikte factoren staan integraal in het rapport. De bronwaarden zijn behouden.

De producentverklaring en het bestaande eigenaarcontract ondersteunen de interpretatie als hoeveelheden in mm per kalenderdecade, na de factor 1000 uit m³/m². Een sluitende componentsom bewijst op zichzelf niet de oorspronkelijke IDF-periodebetekenis of tekensemantiek. De formele, aan de ontvangst gebonden beoordeling van bronfamilie, periode en teken blijft daarom open. De vergelijkingsadapter en selectiepoort zijn niet met een zelfgemaakte toelatingsverklaring gepasseerd. Onderstaande getallen zijn conditionele referentiediagnostiek onder de genoemde conventie.

| Controle over alle 41.580 regels | Resultaat |
|---|---:|
| Maximale afwijking van de native afgeleide rekenregels | 1,44 × 10⁻⁸ mm |
| Grootste absolute BDGETACT minus vijfcomponentensom | 1,701 × 10⁻⁶ mm/decade |
| HRU-decades met dat residu groter dan 10⁻⁴ mm | 0 |
| Grootste absolute opgetelde jaarlijkse BDGETACT-afwijking | 2,812 × 10⁻⁶ mm |
| TACT groter dan TPOT met meer dan 10⁻⁶ mm | 3.834 regels |
| TACT groter dan TPOT met meer dan 10⁻⁵ mm | 0 regels |
| Grootste TACT-overschrijding | 7,31 × 10⁻⁶ mm/decade |

BDGETACT en de vijfcomponentensom zijn hiermee numeriek verenigbaar voor deze selectie en periode. Dat rechtvaardigt verder brononderzoek, maar nog geen omwisseling van de primaire doelvariabele. De huidige doelfunctie blijft de vijfcomponentensom gebruiken.

De kleine TACT-overschrijdingen zijn verenigbaar met afronding in afzonderlijk opgeslagen brontermen. Ze zijn geen aangetoonde fysieke negatieve stress. Er is niets afgeknipt of met een absolutewaarde gecorrigeerd. Fracties worden alleen berekend bij een positieve TPOT boven 10⁻⁶ mm; jaar- en seizoensfracties gebruiken de ratio van de gesommeerde hoeveelheden. Een ongewogen gemiddelde van decadische stressfracties zou perioden met vrijwel nul vraag te veel invloed geven.

## Jaarsommen en componentverdeling

Onderstaande gemiddelden wegen de drie HRU's per profiel gelijk en middelen daarna over alle 55 jaren, inclusief het apart gemarkeerde jaar 2024. Het zijn geen oppervlaktegewogen nationale schattingen en geen effecten van beregening: tussen de geselecteerde profielen verschillen ook bodem en hydrologie. Bodem/plas en interceptie/beregeningsverlies blijven de bestaande vergelijkingsconventies, geen gelijkstelling van hun fysische processen.

| Profiel | Totale ET | Transpiratie | Bodem + plas | Interceptie + beregeningsverlies | Gift |
|---|---:|---:|---:|---:|---:|
| Bouwland beregend | 537,6 | 254,3 | 178,5 | 104,8 | 27,8 |
| Bouwland onberegend | 470,5 | 204,8 | 219,2 | 46,5 | 4,0 |
| Gras beregend | 563,1 | 314,3 | 172,9 | 76,0 | 14,3 |
| Gras onberegend | 544,3 | 301,6 | 163,4 | 79,2 | 1,5 |
| Mais beregend | 553,7 | 265,2 | 233,1 | 55,5 | 9,6 |
| Mais onberegend | 518,1 | 244,9 | 208,4 | 64,9 | 2,0 |
| Natuur onberegend | 523,9 | 242,3 | 122,4 | 159,2 | 0,0 |

Alle getallen zijn mm/jaar onder de expliciete diagnostische tekenhypothese. PSGW en PSSW blijven afzonderlijk beschikbaar in de onderliggende tabellen. De interceptiebijdrage is bij deze natuurselectie relatief groot. Zonder eenzelfde-HRU-SWAP-reeks is dat nog geen bewezen onwaarschijnlijke componentverdeling. Het is wel een reden om bij een latere ET-fit zowel transpiratie als bodem- en interceptieverdamping te blijven controleren.

De laagste en hoogste individuele HRU-jaarsommen zijn 198,3 en 672,8 mm. De lage uiterste waarde ligt in het hieronder gemarkeerde jaar 2024. Een gemiddelde ET-fit zou deze proces- en tijdsvariatie kunnen verbergen; alleen totale ET rapporteren is onvoldoende.

## Beregening en de beperking van een representatieve beheerklasse

Zeven van de negen landbouw-HRU's met een onberegend modelprofiel bevatten feitelijke referentiegiften. Het gaat om 224, 826, 3019, 3487, 5432, 5999 en 8622. Bij ieder van deze zeven is de jaarlijkse gift in ten minste één jaar groter dan de bestaande selectiedrempel van 1 mm. Een SWAP-kandidaat met nul gift zou in zo'n jaar dus terecht op de giftcontrole worden geblokkeerd.

De oorspronkelijke ledenoppervlakken geven een gedeeltelijke verklaring. HRU 224 heeft bijvoorbeeld 13,94% statisch als beregend gelabeld ledenoppervlak, ondanks het onberegende representatieve modelprofiel. De gemiddelde referentiegift is 11,18 mm/jaar en de hoogste jaargift 22,52 mm. Voor 5432 is het beregende ledenoppervlak 14,23% en de gemiddelde gift 5,14 mm/jaar. De binaire modelklasse kan dus een gemengde HRU-support voorstellen.

Dat is niet de volledige verklaring. HRU's 3019 en 5999 hebben in de vastgelegde Work B-momentopname nul beregend ledenoppervlak, maar wel referentiegiften. HRU 8434 heeft een beregend modelprofiel, nul statisch beregend ledenoppervlak en toch giften in een deel van de reeks. Het statische label is daarom geen bewezen historische beheerkalender. De exacte reden kan met deze reeks niet worden vastgesteld; veranderde invoersnapshots, tijdafhankelijk beheer of een verschil tussen label- en giftsemantiek moeten aan de oorspronkelijke bron worden getoetst. Er zijn geen nieuwe labels verzonnen en geen giften verwijderd.

De drie natuur-HRU's hebben zowel nul statisch beregend ledenoppervlak als nul referentiegift over alle 1.980 decades. De moderne regel natuur nooit beregenen blijft ongewijzigd. Ook 926 en 7036 hebben nul referentiegift en nul statisch beregend ledenoppervlak. Deze vijf HRU's zijn daarmee logische eerste kandidaten voor een managementeenvoudige vergelijking, zodra hun overige pakketten en actieve CRP-route zijn gekwalificeerd. Ze zijn daarmee nog niet toegelaten.

Een toekomstige gemengde landbouwkolom vraagt een expliciete beoordeling van de representatieve gift en de niet-lineaire reactie daarop. Een oppervlaktegemiddelde gift is niet automatisch gelijkwaardig aan het gemiddelde van afzonderlijk beregende en onberegende kolommen. Decadische giften leveren bovendien niet vanzelf een dagelijkse planning. De giften gelijkmatig over tien dagen verdelen zou een nieuwe, onbewezen forcingaanname zijn. De huidige gewasfit mag deze structurele verschillen niet compenseren en de giftguard wordt niet versoepeld.

## Transpiratiereductie, jaarselectie en eindjaarcontrole

Voor april tot en met september is binnen het gemeenschappelijke contextvenster 1971 tot en met 2021 een verkennende rangorde gemaakt van de drie onberegende natuur-HRU's. De ratio is de oppervlaktegewogen som van TPOT minus TACT gedeeld door de oppervlaktegewogen TPOT-som. De weging geldt uitsluitend voor de drie geselecteerde natuur-HRU's.

| Jaar | Reductiefractie natuursteekproef april tot en met september |
|---|---:|
| 1976 | 9,00% |
| 1975 | 6,45% |
| 2018 | 6,41% |
| 1990 | 6,01% |
| 2019 | 6,00% |

Dit zijn hoge referentiereducties, geen formeel vastgestelde droge weerjaren. TPOT minus TACT onderscheidt geen droogte van andere opnamebeperkingen, waaronder natte omstandigheden, en bewijst geen specifieke Feddes-gevoeligheid van een SWAP-kolom. Alle weerklassen blijven `UNCLASSIFIED` en alle train-/validatierollen `UNASSIGNED`. Jaarselectie vraagt nog brongebonden meteorologie en hydrologische toestand. De gegevens van 1970 blijven behouden, maar de eventuele modelspin-up is niet als opgelost beschouwd.

De figuur liet tevens een afwijkend eindjaar zien. Bij 15 van 21 HRU's ligt ET in 2024 onder 60% van het gemiddelde over 2014 tot en met 2023. De 60%-grens is een expliciete diagnostische screeningskeuze, geen natuurkundige afkeurgrens. Voor HRU 9551 daalt TPOT bijvoorbeeld naar 6,19 mm/jaar, tegenover gemiddeld 279,58 mm/jaar in de tien voorafgaande jaren. Zo'n vraagverandering kan niet uitsluitend worden verklaard met transpiratiereductie door droogte. Verschillende landbouwreeksen laten vanaf de zomer een sterke verandering zien.

De reeks is kalendertechnisch en qua dekkingsvlaggen compleet, maar die controles bewijzen niet de fysische geldigheid van een lage of nul bronwaarde. De oorzaak blijft open. Er is geen nulvulling, correctie, uitsluiting of klimaatverklaring toegepast. `endpoint-year-diagnostics.csv` bewaart de vergelijking voor alle 21 HRU's. Het jaar 2024 ligt buiten het actuele contextvenster tot en met 2021 en wordt hier niet stil als onafhankelijk validatiejaar aangeboden.

## Betekenis voor de methode en het eerstvolgende experiment

De beperkte parameterhypothese blijft gelijk: alleen RSC en de gekoppelde Feddes-drempels, met de bestaande schaalgrenzen 0,75 tot en met 1,25 en de reeds vastgelegde routecontroles. Worteldiepte, LAI, kalender, bodem, drainage, onderrand, zuurstof/saliniteit en beregening worden niet automatisch vrijgegeven. De bestaande 32 echte SWAP-gevoeligheidsberekeningen uit ET-CAL01 blijven geldig binnen hun beperkte 1971-scope. Deze ontvangst voegt geen nieuwe parametergevoeligheidsrangorde of modelrun toe.

De nieuwe referentie maakt vooral een scherper experiment mogelijk. Begin met dezelfde HRU-identiteit, volledige dagelijkse bronbinding en een vooraf vastgelegd beheer. Gebruik bij voorkeur eerst de vijf hierboven genoemde giftvrije gevallen; toets per pakket of de beperkte RSC/Feddes-route werkelijk actief en toepasbaar is. Voer pas daarna de vijfpuntsgevoeligheidsproef uit. Zet ongevoelige richtingen vast en breid alleen aantoonbaar relevante responsen uit naar het bestaande kwadratische oppervlak met een onafhankelijke SWAP-controle.

Behoud totale ET als primaire doelvariabele met de bestaande jaar-/seizoenscontroles en regularisatie. De nu zichtbare componentverdeling en beheerafwijkingen ondersteunen de bestaande diagnostische component- en giftguards. Ze geven geen reden om parameters of gewichten ruimer te kiezen. Rapporteer equifinaliteit en stabiliteit pas wanneer dezelfde HRU over onafhankelijke volledige jaren is doorgerekend. Vergelijk geen SWAP-HRU 7876 met een andere, toevallig overeenkomstige pilot-HRU.

De concrete uitvoeringsblokkade is aangetoond: de doorsnede tussen deze 21 HRU's en de bestaande 49 C2-onderzoekspakketten is leeg. C2 bewijst bovendien alleen de afgekorte periode 1 januari tot en met 20 december 1971. De pilot heeft nu 55 volledige referentiejaren, maar nog geen gekwalificeerde complete dagelijkse meerjaarsforcing voor dezelfde HRU's. De referentie en de forcing zijn afzonderlijke vereisten. Daarom zijn nul nieuwe SWAP-runs gestart en is geen HRU-specifiek profiel als beter gekwalificeerd.

## Reproductie en evidence

Nieuwe software: `tools.analyze_et_pilot_reference`, met de bestaande ontvanger en zonder nieuwe SWAP-generator. Het uitpakken ondersteunt Windows-backslashes en weigert padtraversal, symlinks en dubbele genormaliseerde namen. De analyse behoudt ruwe waarden, controleert oorspronkelijke afgeleide rekenregels en maakt jaarlijkse, seizoens-, component-, beheer-, support- en jaarresponsdiagnostiek. Een optionele aparte figuurrunner gebruikt matplotlib.

```bash
python -m tools.analyze_et_pilot_reference \
  --archive /pad/HRU21_export_20261021_085909_314.zip \
  --output /nieuwe/map \
  --native-inputs /pad/naar/oorspronkelijk/producentpakket/data \
  --library-file-id libfile_93f3e1c825cc8191bccb59c09286e35e
python -m tools.plot_et_pilot_reference \
  --results /nieuwe/map/results --output /nieuwe/map/reference-overview.png
python -m pytest -q tests/test_et_pilot_reference_analysis.py \
  tests/test_receive_et_reference.py tests/test_et_calibration.py
```

`--native-inputs` is alleen nodig voor de aanvullende leden/supportreconstructie; de ontvangst en ET-diagnostiek werken ook zonder deze optionele audit. Bronidentiteiten, volledige ontvangen numerieke teksten, oorspronkelijke manifesten, receipt en berekende tabellen staan onder `docs/evidence/2026-10-21-et-real-reference/`. De archiefhash is `8634f3f86b38ce100705673d5d27db270569087d775901f7596025d606f9cd8f`. De grafiek staat in `reference-overview.png`. Jaarlijkse en seizoenssommen gebruiken kalenderjaargroepen; bij DJF blijft december bij zijn eigen kalenderjaar.

De gerichte tests controleren kalender- en tekeninterfaces, verliesvrij behoud, componentcontradicties, niet-finiete/onvolledige waarden, giftguards, eindjaarflags en veilige Windows-ZIP-paden. De complete echte upload is daarnaast door de ontvanger en alle beschreven broncontroles gegaan. Er is geen nauwkeurigheidsclaim over SWAP versus MetaSWAP en geen onafhankelijk beoordeelde wetenschappelijke toelating.
