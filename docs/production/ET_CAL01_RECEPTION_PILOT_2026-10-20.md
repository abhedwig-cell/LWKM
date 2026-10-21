# ET-CAL01: ontvangst en beperkte meerjaarsproef

Actualisering 21 oktober 2026: de echte 21-HRU-referentie voor 1970 tot en met 2024 is inmiddels ontvangen en gecontroleerd. Zie [ontvangst en analyse](ET_CAL01_REAL_REFERENCE_2026-10-21.md). De hieronder beschreven status is de historische stand van 20 oktober; er is nog geen feitelijke kalibratie of meerjaars-SWAP-validatie.

20 oktober 2026. Status: ontvangstsoftware en proefselectie geïmplementeerd en getest. Echte referenties zijn nog niet ontvangen. De selectie is voorbereid, maar nog niet uitvoeringsgereed.

PR #12 is inhoudelijk nagelopen en geïntegreerd in `work/lhm-hru-swap-workflow-v1`, mergecommit `a03c48738c446c9b597f0e5105f6c4321db25841`. Dat integreert een onderzoeksmethode, geen feitelijk gekalibreerde gewasprofielen. Er zijn geen onafhankelijke GitHub-reviews ontvangen; de beschreven review is een technische zelfreview. De vervolgimplementatie sluit de native producent aan op de bestaande ET-extractor en comparator. De eerdere 32 SWAP-runs blijven als oorspronkelijke evidence behouden.

## Gecontroleerde ontvangst

`tools.receive_et_reference` ontvangt de oorspronkelijke native `YYYYMMDD.csv`-bestanden met bijbehorende `.sha256` en `hru_support.csv`. De aanvrager geeft de exacte HRU-selectie en periode op. Jaartotalen en decadische populatiegemiddelden worden niet als vervanger geaccepteerd.

De ontvanger controleert het volgende:

- De gehele aangevraagde kalenderreeks bestaat, inclusief variabele slotdecades en schrikkeljaren.
- Iedere oorspronkelijke CSV komt overeen met de uitvoerhash uit zijn bronmarker. Dubbele bron-HRU's of een andere populatie dan het supportbestand worden geweigerd.
- Iedere gekozen HRU staat precies eenmaal in iedere decade. De opgegeven periodelengte is exact juist. Fractionele lengtes worden niet afgerond.
- De dekking ligt tussen nul en één. Een volledig gedekte bronterm is finite; een onvolledig gedekte bronterm blijft leeg. Er is geen nulvulling of normalisatie op de resterende dekking.
- Het complete-vlaggetje is consistent met alle negen dekkingskolommen. Een onvolledige decade mag als onvolledig worden ontvangen; de kalibratieadapter zal haar weigeren.
- De bronbestanden, bronmarkers en support veranderen niet tijdens het lezen.

De gekozen rijen worden met hun oorspronkelijke numerieke tekstvelden doorgegeven. De ontvanger berekent geen nieuwe SVAT-gemiddelden en wijzigt geen afgeronde waarden. Per decade blijven de oorspronkelijke marker, de bron-CSV-hash, de nieuwe selectiehash en de relatie tussen beide bewaard. `receipt.json` legt selectie, periode, herkomstlabel, codehash en alle ontvangen bestandshashes vast.

De ontvangstmap is onveranderlijk. Bij herhaling worden de bronbestanden en de bestaande ontvangst opnieuw gecontroleerd; alleen een identieke ontvangst wordt hergebruikt. Gewijzigde bronnen of gewijzigde code vragen een nieuwe ontvangstmap. Een corrupte bestaande ontvangst wordt geweigerd. Er is geen stil overschrijven van oude onderzoeksresultaten. De oorspronkelijke geldige ontvangst blijft een afzonderlijke snapshot wanneer een nieuwe poging mislukt.

De status is uitsluitend `STRUCTURALLY_VERIFIED_CANDIDATE`. Een label `real_unreviewed` is een expliciete herkomstverklaring van de aanlevering, geen onafhankelijk bewijs van bronauthenticiteit of fysische juistheid. `synthetic` blijft door de geïntegreerde selectieroute herkenbaar. Geen van deze transportlabels verleent wetenschappelijke toelating.

## Van ontvangst naar vergelijking

Voor extractie is een afzonderlijk beoordelingsbestand vereist. Dat moet via de SHA-256 van `receipt.json` aan precies deze ontvangst zijn gekoppeld. Het bevestigt met concrete evidenceverwijzingen:

- eenheid: `mm/calendar_decade`;
- teken: `positive_loss_or_gift`;
- periodebetekenis: `calendar_decade_amount`;
- status: `SEMANTICS_REVIEWED`.

De software vervaardigt zo'n inhoudelijke bevestiging niet automatisch. De meegeleverde synthetische kwalificatie maakt alleen een eigen expliciet als synthetisch herkenbare testbeoordeling. Voor echte gegevens ontbreken deze bewijsstukken nog.

De extractor gebruikt daarna de reeds aanwezige `load_reference`, bewaart PSGW/PSSW afzonderlijk en berekent de vijfcomponentensom en het BDGETACT-residu. Een BDGETACT-residu wordt geen kalibratiefout zonder inhoudelijke beoordeling van die bron. De automatische selectie blijft op totale ET uit de vijf termen gebaseerd.

`select_received` leidt de herkomst uit de ontvangst af. De aanroeper kan in deze route een synthetische ontvangst niet met een losse `real_reference=true`-optie als echt behandelen. Ook is een aan HRU en ontvangst gebonden hydrologie/managementbeoordeling nodig voordat een gewijzigd profiel kan worden voorgesteld. Daarvoor geldt `HYDROLOGY_MANAGEMENT_REVIEWED`, het juiste HRU-nummer, dezelfde receipt-hash en evidenceverwijzingen. De bewijsbeoordeling zelf is geen door de software opgeloste taak. Alle bestaande controles op volledige onafhankelijke jaren, giften, componenten en validatieverbetering blijven gelden. Productie-admission blijft altijd afzonderlijk.

## Voorbereide HRU-selectie

`tools.prepare_et_pilot` gebruikt de bestaande Work B-interfaces, de typed HRU-contexten, de C2-onderzoekscatalogus, de 29 drainage-uitzonderingen en de vier bekende appel-CF-blokkades. De complete populatietabel met 10.242 regels blijft beschikbaar. Er wordt geen nieuwe HRU, donor of representant gekozen.

Voor de beperkte proef zijn 21 bestaande HRU's geselecteerd: drie voor elk van de zeven beheerprofielen. Natuur blijft uitsluitend onberegend. De drie voorlopige screeningsklassen zijn gebaseerd op de bestaande mediane GHG: minder dan 40 cm, 40 tot 80 cm en ten minste 80 cm onder maaiveld. Een GHG is een hoge grondwaterstand; deze klassen bewijzen geen droogteseizoensregime. Die beoordeling vraagt later de volledige dagelijkse grondwaterrespons.

Binnen ieder profiel en iedere GHG-klasse wordt eerst een nog niet gebruikte BOFEK-klasse geprefereerd. Daarna volgt de kleinste afstand tot de mediaan van GHG, netto kwel en de bestaande worteldieptegrens, geschaald met de interkwartielafstand. Bij gelijke uitkomst bepaalt het HRU-nummer de keuze. Dit is een reproduceerbare proefselectie met bodemdifferentiatie, geen nieuwe HRU-medoidprocedure en geen bewijs van nationale representativiteit.

Het resultaat bevat alle zeven profielen en 21 verschillende BOFEK-labels. De huidige modelkolommen vertegenwoordigen volgens de vastgelegde gerealiseerde bodemlookup 78 van de 79 BOFEK-klassen; klasse 35 heeft in deze modelcontextpopulatie geen vertegenwoordiger. De onderliggende SVAT-populatie bevat wel alle 79. De ontbrekende modelklasse wordt niet verzonnen of door een nieuwe kolom vervangen.

Bij 4.236 HRU's verschilt het bodem370-label van de oorspronkelijke representant-SVAT van de bestaande workbook-modelbodem. Dit is een diagnostisch verschil tussen twee bronrollen, geen hier bewezen nieuwe fout in 4.236 modellen. De implementatie behoudt de model-`bodem_id` als authority en bewaart het oorspronkelijke representantlabel apart. Het BOFEK-label voor de proef volgt uit de unieke gerealiseerde bodem370-lookup. De bekende tien afwijkingen met een andere BOFEK2020-lookup worden daarmee niet stil gecorrigeerd. De proef verandert geen modelbodem. Controleer dit onderscheid bij inhoudelijke interpretatie van soil-strata.

De machineleesbare selectie staat in `pilot-hrus.csv`. `population.csv.gz` bevat alle brongebonden model- en representantlabels. De 33 bekende structurele uitzonderingen zijn uitgesloten uit de startselectie. Ook voor de geselecteerde HRU's moeten de actieve PM/CRP-route en de vaste giften nog op pakketniveau worden bevestigd. Dit plan benoemt ze daarom niet als reeds gekwalificeerde RSC/Feddes-experimentpakketten.

## Beschikbare jaren en wat nog ontbreekt

De gezamenlijke tijdsruimte van de actuele typed modelcontexten is 1971 tot en met 2021. In de bestaande meteo-inventaris hebben al deze 51 jaren de verwachte aantallen regen- en ETref-bestanden. De inventaris bevat 58 kalenderjaargroepen; 56 daarvan hebben voor regen plus ETref de verwachte aantallen. Een passend aantal bestanden bewijst niet dat alle dagen uniek en aanwezig zijn, dat de eenheden juist zijn, dat de grondwaterrandvoorwaarden beschikbaar zijn of dat de SWAP-pakketten gekwalificeerd zijn. Sommige andere meteo-variabelen hebben bovendien aantallen boven het aantal kalenderdagen; die kunnen niet zonder nadere bronbinding als één dagelijkse reeks worden beschouwd.

Daarom zijn in `year-availability.json` alle droog/nat-klassen en trainings-/validatierollen nog `UNCLASSIFIED` en `UNASSIGNED`. Er wordt niet op grond van een jaartal of algemene klimaatkennis een trainingsjaar gekozen. De bestaande C2-onderzoekscatalogus ondersteunt alleen 1 januari tot en met 20 december 1971. Er zijn daarmee nog nul volledige vergelijkingsjaren bewezen door de huidige onderzoekspakketten.

Het eerste uitvoeringsbudget is maximaal vijf parameterpunten per geselecteerde HRU voor één toegelaten forcingsequentie: 105 runs. Het plan start die berekeningen niet zolang de brongebonden meerjaarsforcing en referenties ontbreken. Beregende profielen vereisen eerst een vaste en gecontroleerde giftenreeks; een automatische irrigatieplanning mag geen vrije gewasfit compenseren. Het landelijke aantal van 10.242 HRU's is geen kalibratieopdracht in dit vervolg.

## Werkelijk uitgevoerde kwalificatie

De integratieproef maakt 108 native decadetabellen voor de volledig synthetische jaren 2001 tot en met 2003 en drie fictieve HRU's. Daarvan worden twee HRU's verliesvrij ontvangen, opnieuw geverifieerd, met een synthetische semantiekbeoordeling ontsloten en met de bekende synthetische ET-respons vergeleken. Het behouden BDGETACT-residu bedraagt opzettelijk 0,01 mm per decade, samen 1,08 mm. De ET-datafout tegenover de constructie is uitsluitend numerieke afronding. Deze proef bewijst interfacegedrag en claimt geen LHM-nauwkeurigheid.

De geïntegreerde selectie behoudt bij deze synthetische bron het uitgangsprofiel. Unitproeven controleren daarnaast corrupte hashes, ontbrekende perioden, dekkingsfouten, fractionele periodelengte, reproduceerbare proefselectie en uitsluiting van geblokkeerde gevallen. De bestaande 32 dagelijkse SWAP-uitvoerreeksen zijn met de actuele extractor opnieuw geaggregeerd. Het grootste verschil met de behouden decade-ET is circa 7,1 × 10^-15 mm. Er zijn voor dit ontvangstvervolg geen nieuwe engineberekeningen uitgevoerd.

Twee aanvullende controles uit de zelfreview zijn verwerkt: de native adapter rondt een fractionele `days` niet meer af en gevoeligheidsanalyse vereist nu expliciet dezelfde kalender voor alle parameterproeven. De oorspronkelijke ET-berekening en doelfunctie veranderen niet.

## Herhalen en ontvangen

Vanuit de repository in de bestaande lokale Python-onderzoeksomgeving:

```bash
python -m tools.prepare_et_pilot --output /nieuw/et-pilot
python -m tools.qualify_et_reception --output /nieuw/et-reception-test
python -m tools.receive_et_reference receive --source /native/hrudecades \
  --destination /nieuw/ontvangst --hru-ids 224 826 926 \
  --start 1971-01-01 --end 1973-12-31 --data-origin real_unreviewed
python -m tools.receive_et_reference verify --directory /nieuw/ontvangst
python -m tools.receive_et_reference extract --directory /nieuw/ontvangst \
  --hru 224 --review /beoordeelde/semantiek.json --output /nieuw/hru224.csv
python -m tools.receive_et_reference select --directory /nieuw/ontvangst \
  --hru 224 --review /beoordeelde/semantiek.json \
  --context-review /beoordeelde/hydrologie.json \
  --manifest /kandidaten/manifest.json --output /nieuw/profiel224.json
```

De datums en drie IDs in het ontvangstvoorbeeld zijn expliciete invoervoorbeelden. Ze verklaren geen beschikbare echte referentie of goedgekeurde jaren. Het kandidatenmanifest bevat `train_years`, `validation_years` en `candidates`, met per kandidaat `parameters` en `csv`. De bestaande SWAP-pakketgenerator en runner leveren die CSV's; er is geen tweede modelgenerator toegevoegd.

De benodigde vervolgstap blijft: de al geproduceerde native HRU-referenties ontvangen zodra toegankelijk, bronsemantiek beoordelen en dezelfde HRU's aan volledige MET/BBC/giftenpakketten binden. Er is nu geen nieuwe upload of serverhandeling gevraagd. Zonder die echte bytes kunnen dry/wet-validatie en een feitelijke kalibratieverbetering niet verantwoord worden geclaimd.

## Aanvulling: expliciete tekenconventie zonder wijziging van de bronwaarden

De native producent bewaart de oorspronkelijke bronrichting. De afgeleide ET-vergelijking gebruikt daarentegen positieve verliezen en giften. Daarom ondersteunt de semantische beoordeling nu een `source_signs`-object met voor elk van de negen oorspronkelijke variabelen exact een gehele factor +1 of -1. De factor vermenigvuldigt de native mm/decade-waarde. Het is uitsluitend een tekenomzetting; geen eenheidsherschaling, absolutewaarde, temporele interpolatie of correctie van meetwaarden.

De oorspronkelijke kolommen MSW_EBS tot en met BDGETACT blijven in de geëxtraheerde tabel bewaard. `NORMALIZED_<variabele>` bevat de verklaarde vergelijkingswaarde en `SOURCE_SIGN_<variabele>` de toegepaste factor. T, E_SOIL, E_IC, TPOT, IRRIG en het BDGETACT-residu worden uit de genormaliseerde waarden berekend. Ook de PSGW/PSSW-diagnostiek gebruikt deze waarden. De ontvangen bestanden en hun bronhashes veranderen niet.

De review bevat nog steeds `sign: positive_loss_or_gift`; dat benoemt de richting van de vergelijking na omzetting. `source_signs` verklaart hoe iedere bronkolom die richting bereikt. Bij oudere beoordelingen zonder deze sleutel blijft de reeds verklaarde positieve bronconventie gelden, dus alle factoren +1. Een expliciet meegegeven maar onvolledig, leeg, null of ongeldig object wordt geweigerd. De code accepteert geen andere factoren, booleans of willekeurige schaalgetallen. Na omzetting mogen de oorspronkelijke acht ET/vraag/gift-termen geen negatieve verliezen of giften bevatten buiten de kleine bestaande numerieke tolerantie. BDGETACT blijft een afzonderlijke, finite controlebron waarvan een afwijkend teken of residu zichtbaar kan blijven. Er wordt geen conventie afgeleid uit de meerderheid van de getallen.

De SHA-256 van het semantische beoordelingsbestand wordt aan de geëxtraheerde tabelmetadata en het profielselectierapport gekoppeld. Daardoor zijn twee analyses met verschillende tekenverklaringen van dezelfde ontvangst van elkaar te onderscheiden. De gebruikte factoren blijven bovendien als kolommen aanwezig bij CSV-export.

De kwalificatie omvat drie expliciet synthetische bronconventies, elk met 108 decades: volledig positief; negatieve ET/vraag/BDGETACT en positieve giften; en alle negen bronkolommen negatief. Zij leveren na de verklaarde omzetting dezelfde ET-vergelijking. Unitproeven controleren daarnaast niet-nulle positieve én negatieve giften, behoud van ruwe waarden, onveranderde ontvangsthashes en weigering van ongeldige verklaringen. Dit bepaalt niet het feitelijke teken van nog niet ontvangen MetaSWAP-resultaten. Die keuze blijft brongebonden en onbeoordeeld totdat de echte evidence beschikbaar is.

Er is geen nieuwe modelberekening nodig voor deze adapterwijziging. De bestaande doelfunctie, gewasparameters en serverproducent blijven gelijk. De complete testset telt nu 446 geslaagde tests en drie subtests. Evidence: `docs/evidence/2026-10-20-et-sign-contract/`.
