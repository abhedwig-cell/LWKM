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

Deze eerste collectie legt de bekende eendaagse bronproef vast. Ze is geen bewijs dat originele WEL/GHB-budgetten beschikbaar zijn. Het manifest benoemt WEL als schatting. Voeg de werkelijke laag-1-WEL/GHB-budgetbestanden en activiteitsmaskers pas toe nadat zij vanuit de INI en originele pakketuitvoer zijn vastgesteld. Voeg originele LIST/time-discretisatie-evidence toe voor tekens, eenheden en periode. Noem de bestaande geschatte bdgwel niet ORIGINAL_BUDGET.

De schaalbare native postprocessing gebruikt een JSON-plan met:

- `grid` en `membership`: `{path,sha256}`; membership heeft `hru_id,cell_id,area_m2,row,col` met unieke volledige MODFLOW-cellen.
- `model_activity_mask`: gehashte binaire actieve-laag-1-support; alle geselecteerde cellen moeten actief zijn.
- `layer:1`, `units:"m3/day_rate"`, `wel_provenance:"ORIGINAL_BUDGET"`, `ghb_provenance:"ORIGINAL_BUDGET"`, `start`, `end`.
- `signs_evidence`, `units_evidence`, `time_evidence`, `package_coverage_evidence`: elk een werkelijk gehashte bronbinding.
- `intervals`: geordende halfopen intervallen met `start`, `end` en exact de componenten `flf,right,front,ghb,wel`. Iedere component bevat termen met `layer:1`, `positive_multiplier:+1/-1` en `partitions:[{path,sha256}]`. Alleen een expliciet gehashte binaire `activity_mask` mag afwezigheid van een pakket aantonen.

```powershell
python -m tools.process_daily_budget_plan --plan "$Out-budget-plan.json" --output "$Out\daily-budget"
python -m tools.consume_daily_forcing --plan "$Out-consumer-plan.json" --output "$Out\forcing"
python -m tools.bind_daily_catalogue --base "$Out-c2-assets.json" --pairs "$Out\forcing\manifest.json" --output "$Out\daily-catalogue.json"
```

Het consumerplan bindt `hru_flux_shards` en `weather_shards` met path/SHA-256, `start/end` en de lijst `eligible_hrus` uit C2. Weather-shards bevatten `hru_id,date,rad_kj_m2_d,tmin_c,tmax_c,vapour_pressure_kpa,wind_m_s,rain_mm_d,etref_mm_d,wet_fraction`. De strikte serializer gebruikt geen historische neerslagduurcorrectie. De C2-catalogus levert uitsluitend de overige assets; oude MET/BBC worden altijd verwijderd. Daarna kan de bestaande `tools.build_production_packages` en `tools.execute_catalogue_packages` worden gebruikt. Zonder complete forcing ontstaat geen pakket en geen modelrun.

Voor variërende dagelijkse gemiddelde grondwaterfluxen blijft BBC-productie bewust geblokkeerd tot een temporele reconstructie is gekwalificeerd. Gebruik hiervoor geen verborgen interpolatie of einddagverlenging. Bewaar de vier componenten naast de nettoflux en behoud de oude source- en bytekwalificatieregisters.
