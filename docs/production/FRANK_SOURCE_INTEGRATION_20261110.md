# LWKM: oorspronkelijke bronnen en eerste run-lokale rekenstap

Datum: 10 november 2026. Voortzetting vanaf de ontvangen NHI-bronbinding,
commit f504dfda0db32ec22346523a725ae0cbeed39b2e.

## Bronimport

De rechtstreeks geuploade bestanden LWKM_Frank_Pipeline_v02_Bronbeheer(1).zip
en LWKM_Frank_Pipeline_v02_Bronbeheer(2).zip zijn byte-identiek: 119044 bytes,
SHA256 86dcf02933226e78cc5eefc10d11ae6b9067f26056a507110cda48484c904598.
Alle 32 ZIP-items doorstaan de CRC-controle. De twaalf oorspronkelijke Python-
bronnen komen overeen met config/production/frank_original_producers_sha256_v01.json.

Die twaalf bronnen staan nu als afzonderlijke, ongewijzigde bestanden onder
tools/lwkm_frank/legacy in commit 56576662974b59c87ed1d66922757fd551ac1187.
Een lokale .gitattributes voorkomt tekstnormalisatie van deze referentiebronnen.
De vroegere blokkade door ontbrekende toegang tot ZIP-bytes is daarmee gesloten.

## Eerste nieuwe uitvoerroute

Nieuwe adapter: tools/lwkm_frank/msw_basic_run.py.
Configuratie: config/production/frank_msw_basic_v03.json.
Hij gebruikt het bestaande ontvangen run_source_binding.json, met SHA256
90b736e0629302b3fbbb58048f9d3c1af6baa08263b448d4c077b468ad946fbe.
De statische bron blijft run_1970_1979/metaswap/area_svat.inp.
De tijdafhankelijke bronnen komen uit LWKM_run_resultaten_totaal/metaswap.

De standaardproef beslaat kalenderjaar 2020: zes MetaSWAP-variabelen maal
36 decades, samen 216 IDFs. Dit verandert de historische Frank-referentieperiode
1991 tot en met 2020 niet. Deze proef is dus niet rechtstreeks vergelijkbaar met
de dertigjarige referentietabel.

Alleen build_svat_base.execute wordt aangeroepen, met expliciete bronpaden en
een nieuwe uitvoermap. De oorspronkelijke rekenkern is niet gewijzigd.
Het aantal SVATs wordt uit het gebonden area-bestand afgeleid en als expliciete
runtimeverwachting aan de oorspronkelijke reader doorgegeven. De historische
645582 is geen selectiecriterium. De oorspronkelijke controles op 14 kolommen,
unieke positieve IDs, positieve oppervlakken en eindige coordinaten blijven.
Dit is geen nieuwe parser voor een ander MetaSWAP-bestandsformaat.

CONTROLE_MSW_BASIC.cmd leest de area-invoer, controleert bron- en codehashes en
controleert de benodigde IDF-bestandsnamen en datums. De rasterinhoud wordt nog
niet gelezen. MSW_BASIC_CONTROL.json vermeldt dat expliciet. Deze controle
maakt geen hydrologische uitvoer en verandert geen bestaande bronbestanden.

START_MSW_BASIC.cmd start uitsluitend de eerste technische proef. Nieuwe uitvoer:
LWKM_tools/LWKM_Frank_Rebuild_v03/msw_basic_2020_2020.
Een bestaande uitvoermap wordt nooit hergebruikt of overschreven. Er wordt eerst
in een afzonderlijke tijdelijke map gerekend. Alle aangewezen bronbestanden en
code worden voor en na de berekening gehasht. Alleen na een geslaagde uitvoering
met ongewijzigde bronnen wordt de nieuwe map gepubliceerd. Een mislukte run
houdt een tijdelijke map met FAILED.json voor diagnose. Hervatten van een
onderbroken proef is nog niet ondersteund.

Onvolledige rasterdekking blijft als lege hydrologische waarde zichtbaar.
RUN_RECEIPT.json meldt complete_source_svats en all_svats_complete. Een technisch
geslaagde berekening betekent niet automatisch volledige brondekking of
hydrologische kwalificatie. whole_chain_production_enabled blijft false.

## Tests werkelijk uitgevoerd

De drie aangeleverde testscripts test_pipeline.py, test_pipeline_v02.py en
test_release_integrity.py zijn opnieuw uitgevoerd en geslaagd. De negen
producenten ondersteunen --help in de lokale omgeving.

Daarnaast zijn 17 nieuwe unittest-tests geslaagd op Linux met synthetische
IDF-bestanden voor twee SVATs en kalenderjaar 2020. De drie geproduceerde CSVs
zijn byte-identiek aan de rechtstreeks aangeroepen oorspronkelijke rekenkern.
Getest zijn ook NoData, dubbele SVATs, ontbrekende en dubbele IDFs, gewijzigd
area-bestand, gewijzigd bronmanifest, foute bronlocatie, ongeldige periode,
beschadigde rasters, behoud van bronnen, bescherming tegen overschrijven en
het niet publiceren van mislukte uitvoer. Alle 14 Python-bestanden van dit
nieuwe eerste-stappakket doorstaan py_compile.

Niet uitgevoerd: Windows CMD-starters, echte NHI-berekeningen, volledige
1991-2020-regressie en de volledige negenstappenketen. Er is geen algemene
productievrijgave en niets naar main samengevoegd.

## Serverinstructie

Het pakket LWKM_Frank_MSW_Basic_v03.zip bevat een bovenste gelijknamige map.
Plaats die direct onder de bestaande LWKM_tools. Open CMD waar
CONTROLE_MSW_BASIC.cmd staat en voer dat commando uit. Het controlerapport komt
naast het CMD-bestand. De bestaande bronbinding hoeft niet opnieuw te draaien.
De starter gebruikt E:\tools\deltaforge\deltaforge_4\python.exe en NumPy.
Bij een STOP wordt de oorzaak in het JSON-rapport geschreven en exitcode 2 gegeven.
De afzonderlijke berekeningsstarter is voor de technische proef na beoordeling
van het controlerapport; hij start niet de overige acht producenten.

## Nog open

De overige acht producenten zijn nog niet aangesloten op deze adapter.
Aanvullende lookup- en rasterbestanden voor die stappen zijn niet onderdeel van
het eerste-stappakket. De oude Frank-tabel blijft onaangeroerd. Broncode/executable-
authority LWKM-LHM-SOURCE-20261110-01 en de eigenaarvastgestelde identiteit van
statische invoer tussen runs blijven staan; geen nieuwe cross-run-hashverplichting.
