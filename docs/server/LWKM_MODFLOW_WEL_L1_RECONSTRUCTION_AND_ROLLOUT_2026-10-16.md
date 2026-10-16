# MODFLOW WEL, laag 1: reconstructie en historische uitrol (2026-10-16)

## Doel en afbakening

Dagelijkse WEL-waterbalans voor uitsluitend MODFLOW-laag 1 op het gehele LHM 4.3.3-rooster. Beregeningsgiften `Psgw` zitten **niet** in deze WEL-bronnen en worden afzonderlijk behandeld. Output: één `bdgwel_YYYYMMDD_l1.idf` per dag, geen partitiebestanden.

**Belangrijk onderscheid**:
- **1970-1979**: samenvoeging van werkelijk berekende WEL-partitie-IDF's, een referentieproduct.
- **1980-2025**: huidige uitrol is **een historische schatting**, opgebouwd uit een eind-1979-raster plus geschatte tijdsvariatie op zeven cellen. Het is *niet* een onafhankelijke, volledige replay van de acht run-specifieke gegenereerde `nhi.wel`-packages. Niet als exacte oorspronkelijke MODFLOW-uitvoer of volledig wetenschappelijk gekwalificeerd beschouwen.

## Reconstructie- en verificatiegeschiedenis

1. Oorspronkelijke WEL-bronnen: 45 WEL-IPF-bronnen met 5.207 gekoppelde tijdreeksverwijzingen aangetroffen; bronkeuze voor Vitens, WBG en WMD blijkt per run te kunnen verschillen. De gegenereerde `nhi.wel` heeft voorrang boven de oorspronkelijke control-file bij vaststelling van gerealiseerde invoer.
2. Partitieresultaten van `run_1970_1979`: acht `p000..p007` per datum. 3.652 dagen samengevoegd naar één IDF per dag.
3. Server-validatie van die **merge**: 3.652 dagen; 109.560 celwaarden; maximale absolute afwijking `0.000234375000218279 m3/d`; 0 afwijkingen boven `0.002 m3/d`. Dit is alleen een vergelijking van 30 geselecteerde celwaarden, niet van alle rastercellen of toekomstige voorspellingen.
4. Historische laag-1-inventaris van 1970-1979: 457 ooit negatieve netto-WEL-cellen, 550 positieve; samen 1.007 niet-nul-cellen. Binnen `filter_lwkm.asc`: 199 negatieve en 250 positieve cellen. Het betreft *netto* celfluxen; positief/negatief binnen één cel kan uit meerdere bronnen ontstaan.
5. Expliciete `Randflux_l1`- en `BRUINKOOL_L1`-bijdragen zijn in referentieproeven met kleine afwijkingen gekoppeld. In een geïntegreerde 1978-kandidaat waren 945 cellen expliciet gevuld, zeven variërende winningcellen voorspeld en 55 broncellen bewust nog niet voorspeld. Een servercontrole op 1978-01-01 rapporteerde nulafwijking op nulcellen en expliciete cellen en circa `1.5e-8 m3/d` maximale afwijking op de zeven voorspelde cellen; de 55 uitgesloten cellen werden **niet** gevalideerd.
6. Historische test van de zeven variërende winningcellen met bronreeksen en gefitte gewichten: jaar 1978 als holdout maximaal `0.000308 m3/d` over 2.555 dagwaarden; **vijf van zeven individuele filtergewichten zijn niet uniek identificeerbaar**. Dit is geen bewijs voor toekomstige broncombinaties.

Deze afzonderlijke bewijzen mogen niet worden opgeteld tot de claim dat de volledige 1980-2025-reconstructie gevalideerd is.

## Operationele uitrol: contract

Broncode:
- `tools/modflow/wel_l1_rollout/run_wel_l1_1980_2025.ps1`
- `tools/modflow/wel_l1_rollout/LWKM_WEL_Uitrol.cs`

Benodigde run-data (niet in Git opgenomen; afkomstig uit het op 2026-10-16 aangeleverde en gebruikte uitrolpakket `LWKM_WEL_L1_1980_2025_UITROL.zip`):
- `anker_19791231.csv`: zeven celankers voor het eind-1979-referentiedebiet;
- `variabele_cellen_1980_2025.csv`: voorspelde dagelijkse debieten voor de zeven cellen;
- `celmodel_controle.csv`: onderzoeksrapport over serie-rang en historische residuen, alleen audit;
- reeds samengevoegd `bdgwel_19791231_l1.idf` in de doelmap.

De eerste twee CSV's zijn **essentiële invoer**, niet afleidbaar uit de twee gecommitte bronbestanden alleen. Bewaar het originele uitrolpakket en kwalificeer de afzonderlijke bestanden inclusief SHA-256 voordat ze onderdeel van een admitted productieproduct worden. Verander de datasets niet zonder versiebeheer, nieuwe controles en expliciet besluit. Omdat de inputdata niet in de repository staan, is de Git-versie op zichzelf nog niet zelfstandig uitvoerbaar.

Standaard root:
`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow`

Output:
`<root>\bdgwel\bdgwel_YYYYMMDD_l1.idf` en `LWKM_WEL_L1_UITROL_STATUS.csv`.

## Serverinstructie

Plaats beide scripts en de twee benodigde CSV's in dezelfde map op de NHI-server (Windows PowerShell + .NET; geen Python). Gebruik de standaardmap voor het al aanwezige referentie-IDF.

Kleine proef:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_wel_l1_1980_2025.ps1" -Start 1980-01-01 -End 1980-01-03
```

Volledige reeks:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_wel_l1_1980_2025.ps1" -All
```

De runner controleert IDF-geometrie (1124 x 1300), zeven celankers, zeven modelupdates per dag en eindige waarden. Output wordt via tijdelijke `.partial` geschreven; bestaande IDF's worden standaard overgeslagen. `-Overwrite` alleen na gecontroleerde heruitrol. De oorspronkelijke referentiedagen vóór 1980 vallen buiten het toegelaten datumbereik. Controleer vooraf opslag (orde 100 GB voor de volledige nieuwe periode), beschikbare .NET compiler en schijfrechten.

## Rekensemantiek van de huidige schatting

`WEL_est(c,t) = WEL_ref(c,1979-12-31)` voor alle cellen behalve zeven geselecteerde.

Voor die zeven geldt:
`WEL_est(c,t) = WEL_ref(c,1979-12-31) + Q_model(c,t) - Q_model(c,1979-12-31)`.

De run gebruikt dus bewust **geen** nieuwe bron-tot-laagtoekenning voor de overige cellen en doet geen herinterpretatie van de latere `nhi.wel`-varianten. Tijdreekswaarden na de laatste brondatum zijn bij de bereiding van de meegeleverde model-CSV constant gehouden. Nieuwe winningen, veranderde winlocaties, gewijzigde runbronkeuze en andere putmengingen kunnen gemist worden.

## Status en toelating

- Referentie-merge: operationeel uitgevoerd; 30-cel regressie geslaagd.
- Onderzochte variërende bronnen: historische holdout geslaagd, beperkte identificeerbaarheid.
- Uitrol 1980-2025: **estimate / not admitted as historical equivalence**; de Windows-uitvoering van deze nieuwe runner was bij oplevering van de ZIP nog niet bevestigd.
- Niet claimen: nul residu voor alle cellen/alle jaren, exacte oorspronkelijke bronverdeling of bewezen historische invoerequivalentie.
- Houd ruwe brongegevens, gegenereerde `nhi.wel`, scripts en outputs traceerbaar volgens `docs/governance/LWKM_FILE_QUALIFICATION_POLICY_2026-10-02.md` en `docs/governance/LWKM_PRODUCTION_CHAIN_QUALIFICATION_PROTOCOL_2026-10-02.md`.

## Beslispunt

De projecthouder heeft op 2026-10-16 gevraagd deze pragmatische uitrol nu operationeel mogelijk te maken en verdere bronanalyses te stoppen. Dit is **toestemming voor een geschatte werkreeks, geen wetenschappelijke admission van exacte reconstructie**. Toekomstige gebruikers moeten de schattingsstatus behouden in metadata, verslaglegging en interpretatie van de LWKM-waterbalans.
