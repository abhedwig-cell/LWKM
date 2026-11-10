# LHM-rundefinitie: inhoudelijke vergelijking van 8 INI's
Datum 2026-11-10. Onderzocht: door projecteigenaar aangeleverd `LWKM_LHM_RunDef_resultaten_v01.zip` met `lhm_ini_index.csv`, `lhm_ini_references.csv`, `lhm_run_definition.json` (ruim 6 MB uitgepakt).

## Geobserveerde uitkomsten
- 8 verzamelde INI-bestanden, 6 unieke SHA256-identiteiten, 11.895 geparseerde toewijzingen, 6.295 gedocumenteerde padverwijzingen.
- 1980–1989 en 2010–2019 byte-identiek; 1990–1999 en 2000–2009 byte-identiek. Bestandsnaam bewijst dus de daadwerkelijk uitgevoerde periode niet.
- Vergelijking van `(section,key,occurrence)` geeft 52 verschillende sleutelvoorkomens: 49 meteorologische jaargangverwijzingen (voornamelijk na 2020) en 3 WEL/onttrekkingsbronverwijzingen. Dit zijn configuratieverschillen tussen kopieën, geen bewijs dat de daadwerkelijke run dezelfde bestanden gebruikte.
- Bij de kopie voor 2020–2023 valt de EV24/RD1 bronverwijzing voor verdamping 2021–2023 op. Laat dit intact tot de daadwerkelijke model-/forcing-route is herleid.
- Herstartsecties zijn aanwezig voor MODFLOW, MetaSWAP, MOZART en DM. MODFLOW verwijst naar laag-1..8-heads, MetaSWAP onder andere naar `metaswap/msw/init/init_svat.out`, daarnaast MOZART- en DM-herstarts. Een declaratie bewijst niet welke concrete datum/snapshot is gebruikt.
- De kopieën liggen onder `LWKM_tools/LWKM_WorkE_SWP_Bronnen/.../prior_run_controls`. Ze zijn niet daarmee bewezen de opstart-INI's in `run_*`.
- `appendage_area_svat`, `appendage_mod2svat`, `appendage_scap_svat` wijzen naar `metaswap/svat_border`. De Frank-basis gebruikt `metaswap/inp/area_svat.inp`. Een SHA256-vergelijking voor beide paden is de volgende controle; byte-identiteit bewijst nog niet automatisch de werkelijk gebruikte configuratieroute.
- In de INI zijn onderscheiden `nlay=8` (MODFLOW) en `nlay=7` (andere component) zichtbaar; zonder sectiesamenhang is dit geen inconsistentie.

## Bestaande broncodeautoriteit is GEEN open blocker
Nieuwste hogere authority op `main`: `docs/governance/LHM_METASWAP_SOURCE_AUTHORITY_2026-11-10.md`, besluit `LWKM-LHM-SOURCE-20261110-01`, commit `5909b182a2a932233d5ade9148a867d6d2db2fdf`. De projecteigenaar stelt `IMODFLOW.ZIP` met SHA256 `9f50b09908a91cf2459899c128390dbff9bd4aa6f4cf84872a5537488ebb2ad9` vast als de gebruikte broncode voor de betreffende LHM-run. Niet opnieuw om executable/buildlog-verificatie vragen. Alleen daadwerkelijke geactiveerde paden, instellingen en uitvoersemantiek blijven inhoudelijk te onderzoeken.

## Levering voor gerichte servercontrole
`tools/lwkm_frank/compare_svat_source_paths.py`: read-only SHA256 van 10 benoemde bestanden in `E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp` versus `...\svat_border`. Geeft `lhm_svat_path_comparison.csv` en JSON samenvatting; onderscheidt BYTE_IDENTICAL, DIFFERENT_BYTES_REVIEW_REQUIRED, MISSING_COMPARISON, zonder correctie/fallback.

Gebruik vanuit een Git checkout:
```cmd
"E:\tools\deltaforge\deltaforge_4\python.exe" tools\lwkm_frank\compare_svat_source_paths.py
```
of vanuit los uitvoerpakket `CONTROLE_LHM_SVAT_PADEN.cmd`. Beide schrijven uitsluitend naar `LWKM_tools/LWKM_LHM_RunDef_resultaten_v01`.

## Reproduceerbaarheidsstatus en volgende acties
1. De acht INI-kopieën en 52 configverschillen zijn nu inhoudelijk vergeleken; de machineleesbare matrix wordt als aparte analyse-export geleverd, **niet als source-INI**.
2. Server: gerichte `inp` versus `svat_border` SHA's; bij verschil niet op basis van bestandsnaam kiezen. Bewaar beide records en rapporteer rol/versie.
3. Server: zoek vervolgens **run-lokale launch/control/log en restart-eindpunten** voor de relevante klimaatperioden. Geen herberekening en geen reconstructie van de interne Deltares-copychain als verplicht bewijs.
4. Bind de aangewezen outputautoriteit `LWKM_run_resultaten_totaal` met de runconfig onder één provenance-register. Mismatch/afwezig bewijs blijft expliciet zichtbaar.
5. Bestaande Frank origineel SVAT-basistabel onveranderd (645.582 SVAT, SHA256 `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`), geen Flevolandcorrectie of nieuwe waterbalansfysica in de baselining.

**Nog niet uitgevoerd**: de nieuwe SHA-vergelijking op NHI, bindend period-run manifest, volledige source refactoring. De lokale source scanner is met synthetische byte-identieke, verschillende en ontbrekende cases getest.
