# Methode voor identificatie van hydrologisch verdachte SVATs

**Status:** CANDIDATE METHOD — grotendeels brongebonden, enkele authority-punten nog open  
**Datum:** 28 september 2026

## 1. Doel

De identificatie van verdachte SVATs is een expliciete stap in de LWKM-workflow.

De methode heeft als doel SVATs te signaleren waarvan de LHM-hydrologie op basis van vooraf vastgelegde kennisregels nader moet worden onderzocht voordat deze informatie wordt gebruikt voor HRU-afleiding en SWAP-invoer.

Een verdachte SVAT is **niet automatisch fout** en wordt **niet automatisch vervangen**.

De procedure bestaat uit drie afzonderlijke stappen:

1. **detectie**: kennisregels bepalen welke SVATs een flag krijgen;
2. **beoordeling**: flags worden onderzocht en eventueel als uitzondering geaccepteerd;
3. **actie**: een afzonderlijk gebruiks-/replacementbeleid bepaalt of en hoe de SVAT downstream wordt gebruikt.

## 2. Bron van de huidige regels

De meest concrete huidige regelset is teruggevonden in de grid-processing workflow onder het blok:

`afspraken okt-25`.

Deze regels worden hieronder als kandidaat-authority vastgelegd.

De periodevariabele in de betreffende workflow is `1991-2020`.

## 3. Kandidaatregels oktober 2025

### Q01 — hoge subinfiltratie

Flag indien:

```text
ontw_netto > 365 mm/jaar
AND binnen LWKM-domein
AND buiten polders-masker
```

Equivalent aan meer dan 1 mm/dag.

Output:

`subinfil_sel.asc`

### Q02 — hoge runoff natuur / niet-landbouw

Flag indien:

```text
runoff < -548 mm/jaar
AND landbouwmasker = 0
```

Volgens commentaar in het script: meer dan 1,5 mm/dag runoff voor natuur.

Outputdeel:

`runoff_sel_natuur.asc`

### Q03 — hoge runoff landbouw

Flag indien:

```text
runoff < -183 mm/jaar
AND landbouwmasker = 1
```

Volgens commentaar: meer dan 0,5 mm/dag runoff voor landbouw.

Outputdeel:

`runoff_sel_landbouw.asc`

De uiteindelijke runoffflag is:

`runoff_sel = runoff_sel_natuur + runoff_sel_landbouw`.

### Q04 — sterke wegzijging

Flag indien:

```text
kwelwegz < -548 mm/jaar
AND binnen LWKM-domein
AND buiten polders-masker
```

Equivalent aan meer dan 1,5 mm/dag wegzijging.

Output:

`wegzijging_sel.asc`

### Q05 — hoge kwel natuur / niet-landbouw

Flag indien:

```text
kwelwegz > 1826 mm/jaar
AND landbouwmasker = 0
AND buiten polders-masker
```

Volgens commentaar: meer dan 5 mm/dag kwel.

Outputdeel:

`kwel_sel_natuur.asc`

### Q06 — hoge kwel landbouw

Flag indien:

```text
kwelwegz > 730 mm/jaar
AND landbouwmasker = 1
AND buiten polders-masker
```

Volgens commentaar: meer dan 2 mm/dag kwel.

Outputdeel:

`kwel_sel_landbouw.asc`

De uiteindelijke kwelflag is:

`kwel_sel = kwel_sel_natuur + kwel_sel_landbouw`.

### Q07 — kwel bij zeer droge grondwatertrap

De oktober-2025-code bevat:

```text
kwelwegz > 1 mm/jaar
AND gt > 7
```

Output:

`kwel_droog_sel.asc`

Het commentaar luidt: `GT7/GT8 with kwel. Original note says "NB alleen 8"`.

Dit is **nog niet volledig production-bound**, omdat `LWKM_makeHRU` een parameter `gt8_sel_asc` verwacht en nog moet worden vastgesteld of de actuele production control `kwel_droog_sel.asc` aan deze parameter koppelt.

### Q08 — GHG boven maaiveld bij landbouw

Flag indien:

```text
GHG < 0 cm-mv
AND landbouwmasker = 1
```

Output:

`ghg_sel.asc`

## 4. Oudere / aanvullende regels

In dezelfde workflow zijn ook oudere of aanvullende regels aangetroffen, onder andere:

- `gt1_sel`;
- `gt2_sel`;
- `gt8_sel`;
- `glg_sel`;
- `dynamiek_sel`;
- zeer hoge kwel/wegzijging op Pleistoceen;
- classificatiegebaseerde `verdachte_cellen.asc`;
- `verdachte_cellen_extra.asc`, onder andere op basis van runoff, ingesneden waterlopen en rivierdrainage.

Deze regels zijn historisch relevant, maar mogen niet zonder review worden samengevoegd met de oktober-2025-regelset.

Voor de canonical methode moet per regel worden vastgesteld:

- actief in huidige productie: ja/nee;
- vervangen door nieuwere regel: ja/nee;
- alleen diagnostisch: ja/nee.

## 5. Huidige gegevensinterface

`LWKM_makeHRU v0.20` leest afzonderlijk:

- `ghg_sel_asc`;
- `gt1_sel_asc`;
- `gt2_sel_asc`;
- `gt8_sel_asc`;
- `kwel_sel_asc`;
- `wegzijging_sel_asc`;
- `runoff_sel_asc`;
- `subinfil_sel_asc`;
- daarnaast `verdacht_asc`.

De huidige `SVAT_INFO_HRU.CSV` bewaart deze afzonderlijke flags. Dat is de gewenste richting: individuele regels blijven afzonderlijk zichtbaar en worden niet alleen tot één ondoorzichtige indicator samengevoegd.

## 6. Reeds gevonden aantallen in de actuele SVAT-set

In de huidige geselecteerde populatie van 427.656 SVATs zijn eerder de volgende aantallen gereconstrueerd:

| regelveld | aantal geflagde SVATs |
|---|---:|
| `ghg_sel` | 2.243 |
| `gt1_sel` | 1.803 |
| `gt2_sel` | 2.069 |
| `gt8_sel` | 3.629 |
| `kwel_sel` | 8.622 |
| `wegzijging_sel` | 3.934 |
| `runoff_sel` | 2.280 |
| `subinfil_sel` | 979 |
| minimaal één regel | **20.934** |

De regels overlappen; de aantallen mogen daarom niet worden opgeteld tot een totaal.

## 7. Canonical uitvoering

De toekomstige workflow voert de detectie uit als een zelfstandige, versieerbare stap:

```text
SVAT_FLEVOLAND_CORR
        │
        ▼
KNOWLEDGE_RULESET <versie>
        │
        ├─ Q01 subinfil
        ├─ Q02/Q03 runoff
        ├─ Q04 wegzijging
        ├─ Q05/Q06 kwel
        ├─ Q07 droge Gt + kwel
        └─ Q08 GHG boven maaiveld
        │
        ▼
SVAT_FLAGS
        │
        ▼
review / exceptions / usage policy
        │
        ▼
SVAT_QUALIFIED
```

De ruleset zelf is code/configuratie en staat onder versiebeheer.

## 8. Verplichte output per run

Per SVAT worden minimaal bewaard:

- SVAT-id;
- waarde van iedere relevante bronvariabele;
- afzonderlijke boolean flag per kennisregel;
- ruleset-versie;
- rule-id;
- toepassingsmasker;
- eventueel exception-id;
- uiteindelijke downstream usage-status.

Daarnaast wordt per run geproduceerd:

- aantal flags per regel;
- oppervlakte per regel;
- overlapmatrix;
- kaartlaag per regel;
- gecombineerde kaart;
- lijst met nieuwe flags t.o.v. vorige canonical run;
- lijst met verdwenen flags;
- exception register.

## 9. Belangrijke ontwerpregel

De gecombineerde indicator `isverdacht` mag alleen als samenvatting worden gebruikt.

De afzonderlijke rule flags zijn authority voor de diagnose.

Dat is nodig omdat:

- verschillende regels een verschillende fysische betekenis hebben;
- uitzonderingen per regel kunnen verschillen;
- downstream gebruik per variabele kan verschillen;
- de reden voor een donor/replacement achteraf zichtbaar moet blijven.

## 10. Nog open voor definitieve admission

De methode is voldoende gereconstrueerd om nu onderdeel te maken van de workflow, maar nog niet volledig production-admitted.

Nog te binden:

1. exacte actuele production control van `LWKM_makeHRU`;
2. betekenis en authority van `polders.asc`;
3. binding `kwel_droog_sel.asc → gt8_sel_asc`;
4. welke oudere regels (`gt1/gt2/gt8`, `verdachte_cellen`, extra regels) naast de oktober-2025-regels nog actief moeten blijven;
5. exacte samenstelling/codering van `isverdacht`;
6. afzonderlijk beleid van flag naar uitsluiten/vervangen/gebruiken;
7. inhoudelijke review van de drempelwaarden en uitzonderingen.

Deze open punten verhinderen niet dat de detectiemethode nu al expliciet als workflowstap wordt vastgelegd. Ze verhinderen alleen dat de huidige historische implementatie al als definitieve canonical ruleset wordt bestempeld.
