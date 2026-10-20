# ET-CAL01: HRU-specifieke actuele verdamping

20 oktober 2026. Status: geïmplementeerde en geteste onderzoeksmethode. Geen feitelijke MetaSWAP-HRU-kalibratie en geen productie-admission.

De hypothese is dat een beperkt aangepaste gewasrespons de actuele verdamping van een bestaande representatieve SWAP-kolom dichter bij het oppervlaktegewogen gemiddelde van haar LHM-celgroep kan brengen. Een HRU is daarbij een groep cellen met bestaande membership en oppervlaktesupport, geen nieuw afgebakend gebied. De bodem, hydrologische schematisatie en donor/representantenkeuze blijven ongewijzigd. Een passend ET-totaal bewijst op zichzelf niet dat wortelopname, bodemvocht of droogtestress juist zijn.

Deze sessie ontwikkelt de methode vóór ontvangst van de decadische referentie, zoals nu expliciet opgedragen. De volgorde uit het oudere referentiecontract wordt daarmee voor methodeontwikkeling vervroegd. De voorwaarde voor een feitelijke HRU-afstemming blijft gelijk: eerst echte brongebonden referenties en wetenschappelijke beoordeling daarvan. De 10.242 HRU's zijn niet gekalibreerd.

## 1. Authority en afbakening

Basis voor deze branch is de actuele geïntegreerde workflow `ee44a4c168c3b5cb163686f7333fe7aee47d766f`, inclusief Work B, C2 en Work D1. Tijdens het werk is de aanvankelijke D1-head `239a422` bijgewerkt naar de inmiddels geïntegreerde bronreview. Gelezen zijn de Work B/C2-resultaten, D1-overdracht, `ET_DECADE_HRU_REFERENCE_CONTRACT_2026-10-20.md`, de oorspronkelijke 4.3.1-bron en de CRP/SWP/BBC/DRA-bestanden van de gebruikte onderzoekspakketten.

Work B reproduceert de bestaande HRU-membership en 36 schema-attributen. Dat is geen bewijs van alle oorspronkelijke verrijkingsproducenten. C2 levert gekwalificeerde onderzoekspakketten met historische forcing tot en met 20 december 1971. D1 onderscheidt pakketvorming, uitvoeringssucces en productie-admission. Deze grenzen gelden hier onverminderd.

De bestaande vaste besluiten blijven gelden: natuur is onberegend; oppervlakteweging gebruikt de bestaande SVAT-support; PSGW en PSSW zijn giften, geen automatisch afgeleide laag-1-onttrekkingen. De vastgelegde BBC-daggemiddeldebenadering en vijfcomponentenrandvoorwaarde worden niet opnieuw ontworpen. In de aanvullende randvoorwaardeproeven worden bewust kunstmatige fouten aangebracht; dat levert geen nieuwe randvoorwaarde-authority op.

De teruggehaalde distributie bevat `source/SWAP.ZIP`, `source/TTUTIL.ZIP` en de Linux-engine. De executable en `libimf.so` hebben exact dezelfde SHA-256 als de eerdere C2-engine/runtime. De engine is hier daadwerkelijk uitgevoerd. Er is geen SWAP5-engine of oudere 4.2.261-executable gebruikt. Alle primaire bindings en broncodehashes staan in de evidence. De aanvullende afhankelijkheid `libintlc.so.5` wordt eveneens vastgelegd.

## 2. Wat de broncode werkelijk berekent

In `MOD_meteo.f90`, subroutines `penmon`, `ETpot` en `ProcessMeteoDT`, hangt de potentiële verdamping af van de gekozen ET-route. Bij `SWETR=0` en `SWCF=2` gebruikt SWAP onder meer gewashoogte, albedo en RSC in Penman-Monteith. Bij `SWDIVIDE=1` gaat effectieve LAI bovendien in de canopyweerstand en verdeling tussen bodem en gewas. Bij `SWETR=1` en/of `SWCF=1` kan RSC geen gelijkwaardige vrije knop worden verondersteld. De experimentadapter weigert daarom die routes.

De canopyweerstand verandert de potentiële transpiratie. Actuele wortelopname volgt vervolgens uit de beschikbare bodemtoestand, wortelverdeling en stressfuncties. In `rootextraction.f90` wordt de Feddes-drempel HLIM3 tussen HLIM3L en HLIM3H geïnterpoleerd op basis van atmosferische vraag. Onder HLIM3 neemt opname af richting HLIM4. De totale transpiratiereductie TPOT minus TACT kan ook natte, zout- en vorststress bevatten. Zij mag dus niet zonder meer als zuivere droogtestress worden benoemd. De extractor bewaart TREDDRY afzonderlijk wanneer aanwezig.

`boundtop.f90` behandelt plasverdamping EPD afzonderlijk van bodemverdamping EACT. `MOD_meteo.f90` verdeelt onderschepte regen en bovengrondse beregening over netto regen en netto gift. `integral.f90` verzamelt interceptie in iintc. `swap_csv_output.f90` schrijft EIC=iintc, EPD=iepd, EACT=ievap, TACT=iqrot en TPOT=iptra. Daarom is de hier gebruikte SWAP-vergelijkingssom:

`ET = 10 × (TACT + EACT + EPD + EIC)`

De factor 10 zet dagelijkse hoeveelheden in cm om naar mm. EIC bevat bij de betrokken beregeningsroute al het onderschepte beregeningswater. Gross minus net irrigation mag niet nogmaals als extra ET worden opgeteld. SWAP modelleert daarmee niet noodzakelijk alle afzonderlijke MetaSWAP-sprinklingprocessen. Het is een vergelijkingsconventie, geen bewezen procesgelijkheid.

Sublimatie blijft afzonderlijk zichtbaar wanneer ESUBLIM is uitgevoerd. De vijf oorspronkelijke MetaSWAP-ET-termen bevatten geen afzonderlijke sublimatieterm. Bij sneeuw/sublimatie moet daarom eerst de referentieconventie worden onderzocht; een schijnbaar sluitende vijfcomponentensom lost dat semantische probleem niet op. De bestaande onafhankelijke waterbalanscontrole wordt hier alleen toegepast op de C2-pakketten waarvoor zij al is ontworpen.

## 3. Parameterkeuze en grenzen

| Parameter | Experiment | Werkingsmechanisme | Voorwaarde |
|---|---|---|---|
| RSC | 0,75 tot 1,25 maal originele waarde | Canopyweerstand en potentiële transpiratie | PM met actieve gewashoogteroute, oorspronkelijke RSC positief |
| HLIM3H en HLIM3L | Eén gezamenlijke factor 0,75 tot 1,25 | Begin van Feddes-droogtereductie bij hoge/lage vraag | SWDROUGHT=1; HLIM4 < HLIM3L ≤ HLIM3H < 0 |

Dit zijn voorlopige onderzoeksgrenzen rond een brongebonden uitgangswaarde. Het zijn geen empirisch vastgestelde onzekerheidsintervallen en geen universeel geldige gewasgrenzen. Vergroten van de bandbreedte vraagt inhoudelijke onderbouwing. Een schaalfactor groter dan één maakt de negatieve HLIM3-drempels sterker negatief en verschuift de start van reductie naar drogere omstandigheden.

RSC en de twee HLIM3-drempels worden als maximaal twee vrijheidsgraden onderzocht. HLIM3H en HLIM3L worden niet onafhankelijk geoptimaliseerd. HLIM4, ADCRH/ADCRL, zuurstof-, zout- en vorstparameters blijven vast. Automatische beregeningsplanning wordt geweigerd: dezelfde stressparameters kunnen ook de irrigatietrigger veranderen. Voor beregende kalibratie moeten eerst een vaste, brongebonden giftenreeks en overeenkomstige managementroute in het bestaande pakketsysteem beschikbaar zijn.

RDS blijft vast omdat dit in de bestaande invoer een bodemgebonden maximale worteldiepte is. Een grotere RDS of veranderde worteldichtheid kan een onjuiste bodem of onderrand compenseren. LAI-, lichtuitdoving-, gewashoogte-, fenologie- en WOFOST-productieparameters blijven eveneens vast. Bij dynamische gewassen beïnvloeden die tegelijk groei, verdeling en vraag; totale ET alleen biedt onvoldoende onderscheid. Interceptieparameters worden voorlopig niet vrij gekalibreerd, omdat de componenten een diagnostische rol hebben en de procesbeschrijvingen verschillen.

## 4. Responsbibliotheek

De ontwerpindex omvat 79 BOFEK-eenheden en zeven managementprofielen: gras, mais en bouwland ieder met en zonder beregening; natuur uitsluitend zonder beregening. Een eerste indeling onderscheidt ondiep, tussenliggend en diep grondwater plus droge, gemiddelde en natte weerjaren. Dat geeft nominaal 4.977 combinaties vóór parameterexperimenten. Alleen bestaande, inhoudelijk toegelaten combinaties mogen worden gevuld. Een lege combinatie is geen nulrespons en wordt niet stil geïnterpoleerd.

Droog/nat wordt later op beschikbare volledige weerjaren en relevante groeiseizoenen geclassificeerd, bijvoorbeeld op de gezamenlijke verdeling van neerslagtekort en referentieverdamping. Het hier beschikbare 1971-fragment wordt niet zonder analyse als droog, gemiddeld of nat gelabeld. Grondwaterregimes worden aan bestaande HRU/BBC-eigenschappen gekoppeld; kunstmatige vaste standen vervangen geen brongebonden regimes.

De implementatie `library_plan` selecteert eerst gekwalificeerde prototypepakketten per bodemfamilie, profiel, grondwaterregime en weerklasse. Binnen een stratum is de huidige keuze deterministisch op BOFEK/case-ID; dit is een technische startselectie, geen bewezen hydrologische medoid over alle BOFEK-responsen. Controleer de representativiteit op vochtvoorraad, capillaire eigenschappen en bestaande bodemparameters vóór een landelijke bibliotheekronde. De bestaande HRU-representanten zelf veranderen niet.

Voor ieder bezet BOFEK-stratum wordt minimaal een uitgangsrun bewaard. De eerste gevoeligheidsronde gebruikt vijf punten: uitgangspunt plus laag/hoog per parameter. Pas bij een relevante respons wordt uitgebreid. De voorlopige uitbreidingsregel is meer dan 5 mm seizoensverschil in ET of een lokale afgeleide groter dan 0,05 mm/dag per schaaleenheid. Negatieve resultaten worden ook bewaard, zodat niet-identificeerbare parameters worden vastgezet.

Voor een kwadratische benadering zijn negen punten op het 3×3-raster gebruikt. Het model bevat intercept, beide lineaire en kwadratische termen en hun interactie. Het past een afzonderlijke ET-respons per decade. Een onafhankelijke SWAP-run op (RSC=1,125; Feddes=0,875) toetst de benadering. De software weigert extrapolatie buiten de schaalgrenzen. Het responsoppervlak versnelt kandidaatselectie; de uiteindelijke kandidaat moet altijd met echte SWAP worden nagerekend. Het oppervlak is geen vervanging voor onafhankelijke validatiejaren.

## 5. Referentie, kalender en doelfunctie

De native producent schrijft per decade-einddatum een `YYYYMMDD.csv` met HRU-regels. De adapter verifieert de uitvoerhash tegen de bijbehorende `.sha256`, unieke IDs, volledige coverage, finite waarden, periodelengte en kalender. De oorspronkelijke negen variabelen en afzonderlijke PSGW/PSSW blijven behouden. Voor verwerking is expliciete bevestiging van periodehoeveelheid, teken en eenheid nodig; een bestandshash bewijst die semantiek niet.

Let op de overdracht: de bestaande compacte D1-samenvatting bevat jaarlijkse HRU-totalen en decadische populatietotalen. Die tabellen zijn **onvoldoende** voor HRU-specifieke decadische afstemming. ET-CAL01 consumeert de native HRU-decadebestanden met hun markers, of een equivalent verliesvrij overgedragen tabel. Er worden geen HRU-decades gereconstrueerd uit populatiegemiddelden of jaartotalen. De grote IDF-rasters zijn hiervoor niet nodig.

De MetaSWAP-vergelijkingssom is MSW_TACT + MSW_EBS + MSW_EPD + MSW_EIC + MSW_ESP. Bodem plus plas en interceptie plus beregeningsverlies worden daarnaast als vergelijkingscomponenten gerapporteerd. BDGETACT minus de componentsom blijft zichtbaar. De selectie gebruikt BDGETACT nog niet als alternatieve doelvariabele: eerst moeten bronsemantiek en residuen werkelijk zijn beoordeeld. Geen van beide totalen wordt stil als exact beschouwd.

Decades zijn 1 tot 10, 11 tot 20 en 21 tot de laatste kalenderdag. De SWAP-extractor selecteert expliciet de gesimuleerde dagen; de begintoestand telt niet mee. Hij weigert gaten, dubbele dagen, gedeeltelijke decades, ongeldige waarden en een onjuiste ET-componentsom. Er wordt niet op basis van vaste intervallen van tien dagen gegroepeerd en niet opgeteld vanuit cumulatieve uitvoer.

Definieer `e_d = (ET_SWAP,d - ET_ref,d) / n_d`, in mm/dag. De onderzoeksdoelfunctie is:

`J = mean(e_d²) + 0,25 mean(b_jaar²) + 0,25 mean(b_apr-sep²) + 0,05 mean(z_p²)`

Hierin zijn de biases eveneens mm/dag over het werkelijk ondersteunde tijdvak en is `z_p = (s_p - 1) / 0,25`. De regelmatige decadecomponent telt iedere decade even zwaar na omzetting naar gemiddelde dagelijkse ET. De jaar- en seizoenscomponenten voorkomen dat binnenjaarse overschatting en onderschatting zonder zichtbare controle tegen elkaar wegvallen. De regularisatie bevoordeelt kleine aanpassingen. De coëfficiënten zijn expliciete voorlopige beleidskeuzes, geen geschatte meetfouten. Controleer gevoeligheid voor deze keuzes zodra de echte referentie beschikbaar is.

TACT, E_SOIL en E_IC krijgen geen extra fitgewicht. Wel blokkeert een absolute jaarlijkse componentbias groter dan 15% van de totale referentie-ET een automatisch profielvoorstel. Dat is een ruime onderzoekscontrole, geen fysische geldigheidsgrens. Beregeningsgiften krijgen evenmin een gewasfitgewicht. Een som van absolute decadische giftverschillen groter dan 1 mm blokkeert het voorstel; een gewasparameter mag een verkeerde gift niet wegregelen. De giftbron blijft alleen in de referentie opgesplitst: SWAP-IRRIG bewijst geen afzonderlijke PSGW/PSSW-herkomst.

## 6. Werkelijk uitgevoerde SWAP-proeven

Drie complete, brongebonden C2-pakketten zijn uit de bestaande evidence hersteld: bouwland 7870 en gras 7876/7929. Alleen de CRP-overlays veranderen. Bodem, BBC, DRA, meteo, gewaskalender en gewasroute blijven in de gewasproeven gelijk. De periode is 1 januari tot en met 20 december 1971, 354 dagen. Dit is geen volledig kalenderjaar en bevat geen onafhankelijke droog/nat-validatie.

De sessie omvat 27 rasterproeven, drie onafhankelijke tussenpuntproeven en twee bewust kunstmatige randvoorwaardeproeven. Alle berekeningen bereiken de vereiste einddatum. De drie uitgangsruns reproduceren alle numerieke C2-uitvoerwaarden exact. De onafhankelijke dagelijkse waterbalans wordt naast de SWAP-voltooiingsmelding gecontroleerd. Exacte rekentijden, maximale balansafwijkingen en alle dagelijkse reeksen staan in de evidence.

| HRU | Uitgangs-ET, mm | ET bij RSC hoog minus laag, mm | ET bij Feddes hoog minus laag, mm | RMSE tussenpunt kwadratisch, mm/decade |
|---|---:|---:|---:|---:|
| 7870 bouwland | 406,48 | -17,230 | 0,359 | 0,0518 |
| 7876 gras | 505,14 | -25,142 | 0,000 | 0,0154 |
| 7929 gras | 547,80 | -32,596 | 1,384 | 0,0514 |

Hoog en laag betekenen 1,25 en 0,75 maal de oorspronkelijke parameter, met de andere schaalfactor op één. Deze verschillen zijn periodeverschillen, geen nationale foutmarges of verwachte kalibratieverbeteringen.

RSC heeft in deze pakketten de grootste ET-invloed. Voor 7876 is Feddes onder deze condities volledig ongevoelig; de kleinste singular value van de lokale ET-Jacobiaan is nul. Voor 7870 is de verhouding kleinste/grootste singular value ongeveer 0,025, dus ook daar is de tweede richting zwak bepaald. Voor 7929 is deze verhouding ongeveer 0,287 en verschillen de responsvormen beter. Dit is een lokale, modelmatige identificeerbaarheidsdiagnose. Ze bewijst geen identificeerbaarheid tegenover een echte LHM-referentie met bron- en representatiefouten.

Bij 7870 verandert TPOT minus TACT tussen de RSC-eindpunten met ongeveer -53,76 mm. Dat kan vooral ontstaan doordat RSC de potentiële vraag verandert. Deze uitkomst is dus geen zelfstandig bewijs dat de bodem minder droog wordt. TREDDRY en de bodemtoestand moeten mee worden beoordeeld. Bij dynamisch gras kan de aangepaste opname via groei ook op latere potentiële vraag terugwerken.

In de twee aparte randvoorwaardeproeven voor 7870 verandert een kunstmatige toevoeging van 0,01 cm/dag aan de opgelegde QBOT-reeks ET met +1,0335 mm. Het vermenigvuldigen van de bestaande DRARES-waarden met 0,8 verandert ET met +0,0387 mm. Dit zijn uitsluitend lokale foutproeven. Een kleine invloed hier sluit grote effecten in andere bodem/grondwaterregimes niet uit. De originele vijfcomponentenreconstructie en tekenconventies worden hiermee niet herzien.

## 7. Synthetische kwalificatie en selectieregels

Een apart reproduceerbaar programma maakt expliciet synthetische jaren 2001 tot en met 2003 met een bekende parameterrespons. Het toetst parameterherkenning op trainingsjaren en beoordeling op een apart validatiejaar. Deze synthetische functies zijn geen SWAP-berekeningen en geen ontvangen MetaSWAP-reeksen. De positive-path-test simuleert uitsluitend binnen de test een bevestigde referentiestatus. Het gepubliceerde rapport labelt alle reeksen als synthetisch en telt nul feitelijke HRU-kalibraties.

De vijf scenario's zijn: bekende parameters terugvinden; feitelijke toelating op synthetische referenties blokkeren; ET-compensatie tussen T en bodemverdamping detecteren; een afwijkende beregeningsgift blokkeren; en een verslechtering in het onafhankelijke jaar afwijzen. Unitproeven toetsen daarnaast niet-identieke kalenders, schrikkeldekaden, ongeldige parameters, niet-actieve ET-routes, extrapolatie en vrijwel identieke gevoeligheidsrichtingen.

`select_profile` vereist disjuncte, volledige trainings- en validatiejaren en een aanwezige landelijke uitgangsrespons. De keuze minimaliseert de geregulariseerde trainingsscore onder daadwerkelijk doorgerekende kandidaten. Een afzonderlijke data-score op validatiejaren moet beter zijn dan die van de uitgangsparameters. De uitkomst bevat ook jaargewijze beste profielen en bijna even goede alternatieven, zodat instabiliteit en equifinaliteit zichtbaar blijven. Een strikt betere gemiddelde validatiescore alleen bewijst nog geen robuustheid in iedere weerklasse.

Zonder echte referentie, geverifieerde hydrologische/managementcontext, verbetering op onafhankelijke jaren en geslaagde gift/componentcontroles blijft de toegepaste keuze op het uitgangsprofiel. Een geslaagd voorstel krijgt alleen de status `RESEARCH_PROFILE_PROPOSED`; productie-admission blijft altijd false. Bij lokaal niet-identificeerbare Feddes-respons moet die factor in de kandidaatset op één blijven. Een ruimere gewasparameterlijst is hier niet gerechtvaardigd.

## 8. Uitvoering en aansluiting op bestaande software

De nieuwe software bouwt geen tweede SWAP-generator. `overlay` ontvangt een bestaand, volledig samengesteld pakket en wijzigt alleen de expliciet toegestane actieve CRP-waarden. Alle oorspronkelijke inputhashes blijven in `et-overlay.json`. `run_experiment` gebruikt `tools.execute_swap_candidate.execute`; de bestaande pakketgenerator, typed HRU-context en preflight blijven de route voor nieuwe pakketten. De C2-waterbalanscontrole wordt hergebruikt.

Vanuit de repository:

```bash
python -m pytest -q
python -m tools.qualify_et_cal01 --output /nieuw/et-cal01 \
  --executable /pad/swap_431 --runtime /pad/intel-libs
python -m tools.qualify_et_synthetic --output /nieuw/et-synthetic
python -m tools.et_calibration generate --source /bestaand/pakket \
  --output /nieuw/experimenten --factorial
python -m tools.et_calibration run --source /bestaand/pakket \
  --executable /pad/swap_431 --library-path /pad/intel-libs \
  --output /nieuw/een-run --rsc-scale 1.125 --feddes-scale 0.875 \
  --start 1971-01-01 --end 1971-12-20
```

De kwalificatierunner herstelt precies de drie gebruikte C2-pakketten op hash, inclusief meteo. Er zijn geen nieuwe serveruploads nodig om deze proeven te herhalen. Gebruik een nieuwe uitvoermap. Bij herhaald onderzoek kunnen identieke pakketten via de bestaande ketencache worden beheerd; deze experimentrunner overschrijft nooit bestaande resultaten en claimt geen eigen herstartcache.

De Linux-runtime werd uit `intel-cmplr-lib-rt 2026.2.0` verkregen; de `libimf.so`-hash stemt overeen met C2. De workflow verifieert de daadwerkelijke gedeelde bibliotheken in de bronbinding. Er is in deze sessie geen nieuwe Windows-kalibratie-EXE geleverd. De gevraagde software is een lokale Python-onderzoeksketen met de bestaande SWAP-engine.

## 9. Protocol bij ontvangst van echte referenties

1. Ontvang de native HRU-decades en markers met producentidentiteit, bestaande support en unit/sign/period-kwalificatie. De jaarlijkse compacte samenvatting volstaat niet. Controleer ontbrekende decades en HRU's zonder nulvulling of gewichtherschaling.
2. Beoordeel BDGETACT versus de vijf ET-componenten per decade, seizoen, jaar en support. Onderzoek afwijkingen vóór het kiezen van een primaire alternatieve totale-ET-bron. De huidige code blijft op de componentsom.
3. Koppel alleen dezelfde HRU-identiteit, versie en managementroute aan het SWAP-pakket. Controleer bodem, drainage, dagelijkse BBC, meteo en beregening. Historical nature-irrigation wordt een uitzondering voor beoordeling, geen automatische wijziging van de productieregel.
4. Kies volledige trainingsjaren met droge, gemiddelde en natte situaties en onafhankelijke validatiejaren. Behoud een spin-up en sluit die uit van de fit. De huidige 1971-pakketten leveren deze meerjaarsdekking niet.
5. Bouw eerst de prototypes en vijfpuntsgevoeligheden. Zet ongevoelige parameters vast. Breid alleen relevante combinaties uit; valideer het oppervlak met een echte tussenpuntberekening.
6. Selecteer kandidaten met de vaste doelfunctie en rapporteer jaargewijze keuzes, alternatieven, ET-componenten, TREDDRY, TPOT-reductie en giften. Controleer kwetsbaarheid voor grondwater/drainagefouten afzonderlijk. Verander nooit de hydrologie om een gewasfit te verbeteren.
7. Reken de gekozen kandidaat en het nationale uitgangsprofiel op onafhankelijke jaren door. Een HRU-specifiek profiel is pas aannemelijk beter als de feitelijke vergelijking dit laat zien en de procesdiagnostiek standhoudt. Tot die tijd blijft het nationale profiel behouden.
8. Leg alle bron-, code-, parameter-, engine- en uitvoerhashes vast. Laat wetenschappelijke beoordeling en productie-admission via de bestaande W11-W14-procedure lopen. Een automatische parameterkeuze is daarvoor geen vervanging.

## 10. Wat nog niet is aangetoond

Er zijn geen echte MetaSWAP-HRU-decades ontvangen. Er is geen feitelijke kalibratieverbetering, nationale parametergevoeligheidsrangorde, meerjaarsstabiliteit of validatie voor mais, natuur en beregende landbouw aangetoond. De oorspronkelijke forcingbron en de bekende D1/MET-gates blijven afzonderlijk bestaan. De resultaten ondersteunen een kleine onderzoeksparameterlijst en een werkende kwalificatieketen, geen vrijbrief voor aanpassing van alle gewassen.

De methodische conclusie is concreet: begin met RSC waar die route actief en gevoelig is, en laat een tweede droogteparameter pas toe als droge referentiejaren daar werkelijk informatie over leveren. Anders kan een ogenschijnlijk betere ET-fit een onbepaalde of verkeerd gecompenseerde parameterkeuze verhullen.

De definitieve 32 berekeningen vragen samen 107,49 seconden gemeten engine-uitvoering. De grootste onafhankelijke dagelijkse balansafwijking is 0,000300 mm/dag, onder de bestaande C2-grens van 0,001 mm/dag. Dit zijn lokale rekentijden, geen prognose voor een landelijke bibliotheek.

Evidence: `docs/evidence/2026-10-20-et-cal01/summary.json`, `metrics.csv`, `sensitivity.json`, `boundary-controls.json`, `source-audit.json`, `source-excerpts.txt` en de twee afzonderlijke uitvoerarchieven. `execution-evidence.zip` bewaart werkelijke dagelijkse SWAP-uitvoer met content-addressed pakketinputs; `synthetic-fixtures.zip` bevat uitsluitend de kunstmatige meerjaarsreeksen. `synthetic-qualification.json` legt de vijf testsituaties vast. De volledige repositorytest staat in `tests.log`.

Vervolg op 20 oktober: de native ontvangst, semantische beoordelingsbinding en beperkte selectie van 21 HRU's zijn geïmplementeerd. Zie `ET_CAL01_RECEPTION_PILOT_2026-10-20.md`. Dit voegt geen feitelijke kalibratie of meerjaarsnauwkeurigheidsclaim toe.
