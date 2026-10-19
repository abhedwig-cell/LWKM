# Work A serveruitvoering

Deze opdrachten zijn de opgeleverde serverroute. Ze zijn niet live op de LHM-server uitgevoerd. De Python-onderdelen zijn lokaal getest, inclusief de werkelijke 43-bestandscollectie en verse Q4-uitpakcontrole.

Gebruik de actuele LWKM-repository op de server, Python met `tools/requirements-lhm-hru-swap.txt`, het oorspronkelijke bronmanifest uit deze repository en de werkelijke INI/controlbestanden van de betreffende modelrun. De doelmap moet buiten de bronboom liggen.

```powershell
$Repo = 'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM'
$Out = 'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\WORK_A_20200701'
# Bind hier de werkelijk gebruikte 2020-2022-INI, niet een willekeurige andere decade.
$Ini = Read-Host 'Volledig pad van de werkelijk gebruikte 2020-2022 INI/control'
Set-Location $Repo
python -m tools.server.make_daily_collection_plan --manifest "$Repo\docs\evidence\2026-10-19-work-a\original-day-manifest.csv" --control $Ini --output "$Out-plan.json"
if ($LASTEXITCODE -ne 0) { throw 'Plan creation failed' }
powershell -NoProfile -ExecutionPolicy Bypass -File "$Repo\tools\server\run_work_a.ps1" -Repository $Repo -Plan "$Out-plan.json" -Output $Out
```

De Repo- en Out-paden hierboven zijn installatievoorbeelden. Alleen de oorspronkelijke datapaden in het bronmanifest zijn brongebonden; wijzig die niet op basis van een gok. Een verplaatsing moet met dezelfde hashes worden aangetoond. De collector weigert gewijzigde bronbytes en ontbrekende bestanden blijven als MISSING in het manifest staan. Herhaal de collectieopdracht voor hergebruik. Veranderde controls of inputs vragen een nieuwe uitvoermap.

Gebruik voor WEL en GHB de bestaande dagelijkse gereconstrueerde IDF-producten. Zoek geen oorspronkelijke budgetten en voer de reconstructies niet opnieuw uit. De bestaande GHB-uitroldocumentatie bindt `modflow\bdgghb\bdgghb_YYYYMMDD_l1.idf`; WEL staat in `modflow\bdgwel`. Deze locaties zijn uit eerdere scripts vastgesteld, niet live op de server geverifieerd. Zie het actuele [eigenaarbesluit](../production/WORK_A_OWNER_RECONSTRUCTED_PRODUCTS_20261019.md).

De schaalbare native postprocessing gebruikt een JSON-plan met:

- `grid` en `membership`: `{path,sha256}`; membership heeft `hru_id,cell_id,area_m2,row,col` met unieke volledige MODFLOW-cellen.
- `model_activity_mask`: gehashte binaire actieve-laag-1-support; alle geselecteerde cellen moeten actief zijn.
- `layer:1`, `units:"m3/day_rate"`, `wel_provenance:"RECONSTRUCTED_OPERATIONAL"`, `ghb_provenance:"RECONSTRUCTED_OPERATIONAL"`, `start`, `end`.
- `signs_evidence`, `units_evidence`, `time_evidence`, `package_coverage_evidence`: elk een werkelijk gehashte bronbinding.
- `intervals`: geordende halfopen intervallen met `start`, `end` en exact de bestaande netto-componenten `flf,lat,ghb,wel`, of voor reeds beschikbare face-producten `flf,right,front,ghb,wel`. Iedere component bevat termen met `layer:1`, `positive_multiplier:+1/-1` en `partitions:[{path,sha256}]`. Alleen een expliciet gehashte binaire `activity_mask` mag afwezigheid van een pakket aantonen.

```powershell
python -m tools.process_daily_budget_plan --plan "$Out-budget-plan.json" --output "$Out\daily-budget"
python -m tools.consume_daily_forcing --plan "$Out-consumer-plan.json" --output "$Out\forcing"
python -m tools.bind_daily_catalogue --base "$Out-c2-assets.json" --pairs "$Out\forcing\manifest.json" --output "$Out\daily-catalogue.json"
```

Het consumerplan bindt `hru_flux_shards` en `weather_shards` met path/SHA-256, `start/end` en de lijst `eligible_hrus` uit C2. Weather-shards bevatten `hru_id,date,rad_kj_m2_d,tmin_c,tmax_c,vapour_pressure_kpa,wind_m_s,rain_mm_d,etref_mm_d,wet_fraction`. De strikte serializer gebruikt geen historische neerslagduurcorrectie. De C2-catalogus levert uitsluitend de overige assets; oude MET/BBC worden altijd verwijderd. Daarna kan de bestaande `tools.build_production_packages` en `tools.execute_catalogue_packages` worden gebruikt. Zonder complete forcing ontstaat geen pakket en geen modelrun.

Voor variërende dagelijkse gemiddelde grondwaterfluxen blijft BBC-productie bewust geblokkeerd tot een temporele reconstructie is gekwalificeerd. Gebruik hiervoor geen verborgen interpolatie of einddagverlenging. Bewaar de vier componenten naast de nettoflux en behoud de oude source- en bytekwalificatieregisters.


## Bestaande dagreeksen binden

`python -m tools.server.bind_reconstructed_daily --config bindings.json --output bound`

`bindings.json` bevat `processing_contract` met bovenstaande velden, `controls:[{path}]` en `sources` met exact `flf,lat,ghb,wel`. Iedere bron bevat `directory`, `pattern` (bijvoorbeeld `bdgghb_{date}_l1.idf`), `positive_multiplier`, `provenance` en `semantics_evidence`. `{date}` is YYYYMMDD. Gebruik voor LAT uitsluitend de werkelijk aanwezige nettorasterlocatie; raad geen mapnaam. De processor behandelt LAT dan direct als netto-celflux en neemt niet opnieuw de divergentie.

Het processing-contract bevat `reconstructed_products.wel` en `.ghb`, elk met `method`, een niet-lege `limitations`-lijst en gehashte `evidence:{path,sha256}`. Zie de vastgelegde productdocumentatie in `docs/evidence/2026-10-19-work-a-owner`. Gebruik voor beide provenancevelden `RECONSTRUCTED_OPERATIONAL`. De binder selecteert alleen opgegeven dagen, hasht de bestaande bestanden, meldt ontbrekende dagen en verwijdert een eventueel oud uitvoerbaar plan wanneer de selectie incompleet is. Daarna:

```powershell
python -m tools.server.collect_daily_consumers --plan bound/collection-plan.json --output collected
python -m tools.process_daily_budget_plan --plan bound/processing-plan.json --output daily
```

De volgende stappen zijn de bestaande consumer-, C2-catalogus- en pakketbouwcommando's hierboven. Bestandstechnische Q4-verificatie en operationeel toegelaten reconstructiemethode zijn afzonderlijke beoordelingen. De WEL-beperkingen en GHB-datumdefinitie blijven zichtbaar; originele budgetten zijn geen voorwaarde.


## Actuele vijfcomponentenroute

De aanvullende authority is [Work A vijf componenten](../production/WORK_A_FIVE_COMPONENT_AUTHORITY_20261019.md). Er is geen aparte LAT-map nodig. Het volgende selecteert de bestaande samengevoegde FLF/FRF/FFF/GHB/WEL-reeksen in de vastgelegde mappen, met de bestaande teken-/ruimtelijke omzettingen. Voer geen reconstructiescripts uit.

```powershell
python -m tools.server.make_five_component_config --contract "$Out-contract.json" --output "$Out-five.json"
python -m tools.server.bind_reconstructed_daily --config "$Out-five.json" --output "$Out-bound"
if ($LASTEXITCODE -ne 0) { throw 'Daily binding incomplete: inspect binding-report.json' }
python -m tools.server.collect_daily_consumers --plan "$Out-bound/collection-plan.json" --output "$Out-collected"
python -m tools.process_daily_budget_plan --plan "$Out-bound/processing-plan.json" --output "$Out-daily"
```

`$Out-contract.json` is het hierboven beschreven gehashte processing-contract, zonder `intervals`, met de gekwalificeerde membership, referentiegeometrie, support, periode en reconstructieherkomst. De dagelijkse bronbindings worden door de binder toegevoegd. Periodekeuze binnen 1970-2022; begin met een gedeelde dag waarvoor ook MET volledig beschikbaar is. De generator veronderstelt geen origineel WEL/GHB-budget.

De bestaande dubbele-middernacht-BBC is uitsluitend experimenteel voor variërende daggemiddelden: 98 echte modelproeven hebben het ontbreken van algemeen dagvolumebehoud aangetoond. De standaardconsumer weigert zulke reeksen. Constante eendaagse brongebonden BBC's zijn wel geproduceerd en de bestandskoppeling is getest. Zie het rapport voor de concrete modelbeperking en evidence. Dit vervangt eerdere omschrijvingen die alleen naar een nog te onderzoeken interpolatiebeleid verwezen.
