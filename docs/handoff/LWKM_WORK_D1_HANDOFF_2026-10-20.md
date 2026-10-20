# LWKM Work D1 herstelpunt en overdracht

Datum: 20 oktober 2026. Branch: `work/lwkm-work-d1-20261020`. PR: https://github.com/abhedwig-cell/LWKM/pull/11.

Dit herstelpunt verwijst naar bestaande ontwerpbesluiten; het voegt geen nieuwe wetenschappelijke authority toe. De basis is `212d8c7e9396d62c45f3b26cddd6cefea1cc778d`. Work B-head `1a9e8eef340926ecc45bd7e7a8d3260e3344b6d8` en MetaSWAP-head `4ab5eb139bd412652081e4b2bce64d9c7b9469f4` zijn als voorouders geïntegreerd. PR's 3-7 en 9 waren al geïntegreerd. PR's 8 en 10 blijven afzonderlijk herkenbaar; D1 sluit ze niet zelfstandig.

Lees eerst de drie bijgewerkte centrale documenten onder `docs/production`: ARCHITECTURE_20261019.md, RUNBOOK_20261019.md en REPORT_20261019.md. Daarna LEO_ACCEPTANCE_20261019.md, `config/production/work-d1-contract-v1.json`, de definitieve kwalificatie-evidence en `blockers.json` onder `docs/evidence/2026-10-20-work-d1`.

De code bevat een native compacte MetaSWAP-acceptor, een zelfstandig gebundelde MET-consumer, een zelfstandig gebundelde consumer voor bestaande vijfcomponentenbudgetten, herstartbare ontvangst en een geïntegreerde MET/BBC/pakketworkflow. Windows native-kwalificatie en levering horen bij `.github/workflows/work-d1-windows.yml`. Er is geen Python-installatie op NHI nodig.

De landelijke integratietest gebruikt 427.656 echte supportrecords, alle 10.242 contexten, bestaande C2-checkpoints en originele gewasbronnen. De forcing is expliciet synthetisch. De 29 drainage-uitzonderingen en vier appelboom-CF-gevallen blijven geblokkeerd. Er wordt geen echte nieuwe serverforcing-run of productie-admission geclaimd. De 101 bestaande C2-runs blijven bewaard.

Voor hervatting: ontvang eerst de echte compacte MetaSWAP-export en de brongebonden dagelijkse producten zodra die bestaande resultaten weer toegankelijk zijn. Bevestig de ruwe LHM-unitbinding uit bestaande metadata. Gebruik dezelfde consumenten en hashes; heropen de reconstructies, tekens, area_svat-keuze of BBC-daggemiddeldebenadering niet zonder bewijs van een fout. Geen aanvullende temporele BBC-correctie ontwikkelen.

Voor een nieuwe complete 4.3.1-run is de reeds geïdentificeerde juiste engine/runtime nodig. De helperroute naar SWAP_4.3.1.zip faalde in deze sessie met HTTP 403. De teruggevonden Tools(2).zip-executable is aantoonbaar 4.2.261 en is niet gebruikt als vervanger. De bestaande modelkwalificatie blijft geldig binnen haar oorspronkelijke scope.

Grote echte serverarchieven zijn niet opnieuw gevraagd. Workbook, Template.zip, control_runs(2).zip en METEO_INVENTORY.zip konden uit bestaande verwijzingen worden verkregen. Dat sluit geen inhoudelijke Work B-enrichmentgate zonder toets. De bronidentiteiten en beperkte inventarisevidence zijn opgeslagen; grote rasterpayloads zijn niet gekopieerd.

## Vervolgreview op 20 oktober

De implementatie is opnieuw langs bronbinding, populatie/dekking, MET/BBC-semantiek, drainageperiode en herstartpaden beoordeeld. De opgeslagen codehashes en alle oorspronkelijke D1-evidencehashes zijn opnieuw gecontroleerd. De drie CI-runs op de definitief geteste code staan op success; er zijn geen GitHub-reviewthreads. Dit is een technische zelfreview, geen onafhankelijke wetenschappelijke toelating. Er was geen codewijziging nodig.

De [bronreview](../evidence/2026-10-20-work-d1/source-review.json) legt beide appeltemplates, de vier workbookrijen en alle acht bestaande control-INI-identiteiten vast. Beide appeltemplates missen een CF-tabel en verschillen in RSC (144,0 tegenover 201,3 s/m). De control-INI-bestanden koppelen vapp aan FG zonder een aantoonbare eenheid/schaal. Het oorspronkelijke serverauditpakket is nu gelezen en compact behouden; het bevat pad- en aantallenevidence, geen meteorologische producentmetadata. Deze twee gates blijven dus onderbouwd open. Historische Work A-verslagen verwijzen nu expliciet naar de latere BBC- en WET-besluiten.
