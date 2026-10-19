# Work A: bindend besluit voor bestaande gereconstrueerde dagproducten

De projecteigenaar heeft op 19 oktober 2026 de bestaande dagelijkse gereconstrueerde WEL- en GHB-IDF-bestanden aangewezen als operationele bronnen. Hun reconstructie wordt niet heropend. Het zoeken naar oorspronkelijke dagelijkse WEL/GHB-budgetten valt buiten deze opdracht en het ontbreken daarvan is geen zelfstandige blokkade. Dit besluit vervangt de eerdere tegenovergestelde eisen in Work A-documentatie en bronproefnotities.

## Betekenis en implementatie

De productklasse is `RECONSTRUCTED_OPERATIONAL`, nooit stilzwijgend `ORIGINAL_BUDGET`. De processor accepteert deze klasse zonder onderzoeksopt-in, mits reconstructiemethode, beperkingen en gehashte herkomstevidence zijn gebonden. Ongeclassificeerde schattingen blijven geweigerd. Dagdekking, geometrie, actieve support, eenheden, tekens en bestandsidentiteit blijven verplicht. Dit besluit verleent geen automatische wetenschappelijke toelating aan iedere afzonderlijke tijdreeks.

Bestaande netto-LAT-IDF's kunnen rechtstreeks naast FLF/GHB/WEL worden verwerkt. De vier componenten worden per cel tijdgeïntegreerd, afzonderlijk bewaard en over de HRU-membership gesommeerd. Omrekening is 1000 maal m³/d gedeeld door de vertegenwoordigde volledige MODFLOW-celoppervlakte. Een netto-LAT-raster wordt niet opnieuw gedifferentieerd. Gemengde invoer van LAT én faces wordt afgewezen. MetaSWAP, berging en ontwatering worden niet toegevoegd.

De nieuwe serverbinder inventariseert uitsluitend expliciet aangewezen componentmappen en dagen, schrijft exacte SHA-256-bindingen en een Q0-Q4-collectieplan, en geeft alleen bij complete dekking een uitvoerbaar verwerkingsplan uit. De bestaande collector hergebruikt correcte objecten en controleert hashes opnieuw. De binder reconstrueert geen hydrologische waarden.

## Teruggevonden broninformatie

De bestaande GHB-uitrolbeschrijving geeft `LWKM_run_resultaten_totaal\modflow\bdgghb\bdgghb_YYYYMMDD_l1.idf`, m³/d, positief naar grondwater. Zij gebruikt de head van dezelfde bestandsdatum, statische GHB-parameters en expliciete nulwaarden voor niet-GHB-cellen binnen actieve support. Die nulwaarden worden uit het bestaande product gelezen; de nieuwe processor vult ontbrekende data niet zelf met nul.

Het bestaande WEL-uitrolpakket voor 1980-2025 schrijft naar `modflow\bdgwel`. De beperkingen zijn wezenlijk: ruimtelijk anker 1979-12-31, zeven variabele broncellen, voor andere cellen behoud van ankerflux, voortzetting na laatste brondatum en niet-unieke putgewichten voor vijf cellen. Dit blijft een operationele benadering. De README's zijn ongewijzigd vastgelegd met archief- en memberhashes in `docs/evidence/2026-10-19-work-a-owner/`. Geen van de reconstructies is opnieuw uitgevoerd.

## Uitvoeringsgrens en vervolg

Deze Work-runtime heeft geen toegang tot de Windows G-schijf of een opgegeven serverendpoint. De exacte dagelijkse IDF-bytes en volledige reeksen kunnen hier daarom niet live worden gebonden. De locaties hierboven zijn onderbouwd door bestaande scripts, geen live geverifieerde bestandsaanwezigheid. De afzonderlijke LAT-mapvraag is vervallen door het aanvullende eigenaarbesluit: gebruik de bestaande FRF/FFF-reeksen en verwerkingsregels. Zie WORK_A_FIVE_COMPONENT_AUTHORITY_20261019.md. Gebruik de serverhandleiding en nieuwe binder; geen nieuwe reconstructie is nodig.

De eerdere 43 Q4-bestanden, bronproeven en C2-resultaten blijven behouden. Er is met dit besluit geen nieuwe volledige moderne forcingcombinatie beschikbaar gekomen en geen nieuwe moderne SWAP-run uitgevoerd. Volledige meteorologie ontbreekt nog lokaal. Voor variërende dagelijkse BBC-gemiddelden is de SWAP-puntinterpolatie nog afzonderlijk te kwalificeren; de bestaande strikte guard blijft actief. Dit zijn afzonderlijke resterende uitvoeringsgrenzen, geen eisen om WEL/GHB opnieuw te reconstrueren.

## Verificatie

De volledige lokale suite slaagt: 374 tests en 3 subtests. De nieuwe integratieproef bindt vier bestaande synthetische IDF-reeksen, verwerkt twee dagen, controleert interne LAT-annulering en mm/d, voert de Q4-collectie tweemaal uit en bevestigt hergebruik. Negatieve proeven weigeren gewijzigde hashes, ontbrekende reconstructieherkomst, gemengde LAT/faces en ontbrekende dagen. Dit zijn softwareproeven, geen nieuwe echte-bron- of modelkwalificatie. Het ongewijzigde C2-modelresultaat blijft 101 geslaagde berekeningen.
