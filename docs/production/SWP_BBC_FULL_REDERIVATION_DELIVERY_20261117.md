# SWP/BBC: volledige herafleiding, 17 november 2026

## Opdracht en levering

De projecteigenaar heeft de opdracht tijdens de ontwikkeling gewijzigd: niet bestaande SWP/BBC-bestanden repareren, maar beide producten volledig opnieuw uit de oorspronkelijke bronnen afleiden. De geleverde software volgt deze gewijzigde scope. Oude SWP/BBC-uitvoer en oude BBC-dagcaches worden niet als berekeningsinvoer gebruikt.

Downloadpakket `LWKM_SWP_BBC_Herafleiding_v01.zip`: 146119 bytes, SHA256 `48045ef7a148a3a097611a0072f73dbd9ba9c29926e3a50b06acf00383085df2`.

Bronwijzigingen, oorspronkelijke aangepaste modules, regressietests en git-apply patch: `LWKM_SWP_BBC_Herafleiding_Broncode_v01.zip`, 80638 bytes, SHA256 `4ca6c1a8f4f06630d238e8d03102b87705ee923969a7201fa94e273644a2e414`.

De patch is gebaseerd op `15fedc9b17a1e716372b64f3379c00bb44e1647f`, dat ten opzichte van de oorspronkelijke SWP-broncommit alleen de ontwikkelworkflow toevoegt. De volledige bronwijzigingen zijn in deze ontvangstcommit NIET als afzonderlijke repositorybronbestanden geïntegreerd. De twee ZIP's bevatten de daadwerkelijke nieuwe uitvoerbare Python-code. Deze notitie mag niet als een merge van die implementatie worden gelezen. PR #30 bevat reeds de afzonderlijke BBC FORMAT15-bronwijziging.

## Gedrag van de nieuwe code

- SWP-parameters worden opnieuw uit oorspronkelijke HRU-/SVAT-identiteiten, bodem- en rotatietabellen en de geselecteerde NHI-rasters afgeleid. De gekozen natuurtemplate blijft SWCF=2; de vierklassentabel gebruikt nu SWETR=0 voor natuur, met de bestaande rendererkeuze SWDIVIDE=1.
- Oppervlakte en maaiveld komen uit kolommen 2 en 3 van run-lokale area_svat.inp (m2 en m NAP). De standalone AHN-grid wordt niet meer voor glk/GWLI gebruikt. De zes perioden worden op geselecteerde ID's, XY, oppervlakte en hoogte gecontroleerd. De primaire bron is aan eigenaarhash `352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc` gebonden. Bestaande HRU-aggregatie en GWLI-afronding blijven behouden.
- De daadwerkelijk gelezen rotatie bevat vanggewas buiten het reeds bestaande maïs-beregeningsvenster 16 april t/m 30 september. Alleen na expliciete toetsing van ALLE vanggewasintervallen op niet-overlap behoudt vanggewas SCHEDULE=0. Bij één overlappende dag stopt de generatie wegens ontbrekend schema. Er worden geen beregeningsdata, giftgroottes of drempels verzonnen. Hoofdgewasberegening en de nationale areaaltoekenning worden niet aangepast. Beregende natuur wordt geweigerd, niet stilzwijgend omgezet.
- BBC leest opnieuw de vijf oorspronkelijke dagelijkse MODFLOW-reeksen met de bestaande BBC09 opgeslagen-fluxvlakconventie, volledige celoppervlakken en gebonden IBOUND. Alleen de definitieve QBOT2-notatie gebruikt .15g; rekenwerk, NPY-tussenbestanden en transfer-CSV's behouden de bestaande precisie.
- De nieuwe BBC-route weigert gewijzigde bron-/checkpointidentiteiten bij hervatten. Zij leent geen controlepunten van de oude productie. De twee nieuwe producenten gebruiken één OS-lock en nieuwe outputidentiteit.

Start vanuit de uitgepakte map met de starter:

```cmd
LEID_SWP_EN_BBC_OPNIEUW_AF.cmd
```

Afzonderlijke starters voor SWP en BBC zijn eveneens opgenomen. Interpreter: de reeds gebruikte `E:\tools\deltaforge\deltaforge_4\python.exe`, met NumPy. Geen installatie of netwerkgebruik op de NHI-server.

Nieuwe uitvoer onder `LWKM_rebuilds\SWP07_BBC10_Herafleiding_v01`, met `swp_productie\swp` en `bbc_productie\bbc`. Het kleine terugrapport is `LWKM_tools\LWKM_SWP_BBC_Herafleiding_v01_resultaat\SWP_BBC_HERAFLEIDING_TERUG.zip`. Voor een lege dataset wordt 50 GiB uitvoer plus 5 GiB reserve geraamd; dit is een conservatieve begroting, geen gemeten landelijke uitvoeromvang.

## Werkelijk uitgevoerde tests en begrenzing

107 lokale regressietests slagen. Daarnaast slagen 15 synthetische bronproeven; één Windows-only CMD-test is lokaal overgeslagen. Deze bronproeven zijn opnieuw uitgevoerd uit de definitieve uitgepakte ZIP, inclusief pakketmanifestverificatie. Zij voeren beide echte Python-producenten op kleine synthetische bronnen uit, inclusief nieuwe parameters/rendering, raw IDF-aggregatie, hervatten, bronwijzigingen, gewijzigde gepubliceerde uitvoer, ontbrekende terrainbron, oude onbruikbare uitvoerbestanden en behoud van oorspronkelijke bestanden. Geen wetenschappelijke SWAP-executable gestart.

Testlog `LWKM_SWP_BBC_Herafleiding_Testlog.txt`: SHA256 `28d8b66c45d45001df594a28a0e5c0fd542bd40ba02b6a7d2322b5bfd0fe8b50`.

De eerder geslaagde GitHub-workflowruns op deze branch betroffen de oorspronkelijke baseline plus workflow, NIET de in dit ZIP geleverde nieuwe implementatie. Er wordt geen Windows-CI-kwalificatie van de nieuwe pakketcode geclaimd. Evenmin is hier de nationale NHI-bronpopulatie verwerkt.

MET07, DRA, oude gehashte invoer en de 82 bestaande succesvolle modelresultaten blijven ongemoeid. De nieuwe SWP/BBC-set moet later expliciet in een nieuwe assemblage/campagne worden gebonden. Bestaande succesvolle berekeningen worden niet automatisch onder de nieuwe invoeridentiteit overgenomen. De oude batchstarter 03 blijft geblokkeerd; geen productie-admission, geen LHM-waterbalansheropening en geen merge naar main.
