# Frank/NHI MODFLOW exporter v0.6: 16 fluxkolommen

Projecteigenaarbesluit 4 november 2026: v0.5 was te smal, behoud de 13 dagelijkse bruto-splitsingen plus **getekende nettofluxen LAT, WEL en GHB**. Geen STO, BND of qmodf.

De in deze sessie daadwerkelijk gebouwde en synthetisch geteste Python-software staat in gebruikersartifact `LWKM_Frank_LHM_Server_v06_16_FLUXEN.zip`. Softwarecode is nog geen Git-sourcecommit; dit document legt het contract en de bijbehorende teststatus vast.

## CSV-velden en eenheden
Identificatie: `SVAT,Opp_svat_m2,X_RD,Y_RD`.

**Exact 16 fluxwaarden** (cumulatief m³ over de opgegeven periode per volledige MODFLOW-cel 62500 m²):
- `RIV_SYS1_ONTWATERING_m3` t/m `RIV_SYS4_ONTWATERING_m3` (4)
- `RIV_SYS1_INFILTRATIE_m3` t/m `RIV_SYS4_INFILTRATIE_m3` (4)
- `DRN_SYS1_ONTWATERING_m3` t/m `DRN_SYS3_ONTWATERING_m3` (3)
- `FLF_KWEL_m3`, `FLF_WEGZIJGING_m3` (2)
- `LAT_NETTO_m3` (uit reeds gereconstrueerde dagelijkse QLAT=FRF+FFF), `WEL_NETTO_m3`, `GHB_NETTO_m3` (3).

RIV: op de *dagelijkse netto-celflux* `infil=max(q,0)`, `ontw=max(-q,0)`. DRN: uitsluitend ontwatering en fout bij positieve dagbudgetwaarden boven tolerantie. FLF: positieve = kwel, negatieve = wegzijging. LAT/WEL/GHB getekend; geen opsplitsing. Bruto-richting vóór jaarlijkse/meerjarige accumulatie, zodat wisselende tekens niet wegvallen. Controleer identiteit `RIV_signed=infil-ontw`, `FLF_signed=kwel-wegzijging`. Geen impliciete SVAT-oppervlakteschaling en geen HRU-aggregatie in deze stap.

## Uitvoering
Directory op NHI-server: `LWKM_tools/LWKM_Frank_LHM_Server_v06`. CMD:
```cmd
CONTROLE_MODFLOW_2020.cmd
START_MODFLOW_PROEF_2020.cmd
```
Na controle resultaten:
```cmd
CONTROLE_MODFLOW_KLIMAAT.cmd
START_MODFLOW_KLIMAAT.cmd
```
Uitvoer afzonderlijk `LWKM_run_resultaten_totaal/frank_export_modflow_bruto_v06/MF_SVAT_BRUTO_16_2020_2020.csv` etc. Nieuwe `v06_16_daily_gross_plus_qlat_wel_ghb` cacheversie om verouderde v0.5-checkpoints te blokkeren. Reeds voltooide bronlezing v0.5 kan niet de oorspronkelijke qlat/wel/ghb jaarreeksen reconstrueren; v0.6 moet de bron opnieuw doorlopen.

## Tests
In container 4 nov 2026:
- `python test_gross_split.py`: PASS, inclusief alle 16 CSV-kolommen, twee dagelijkse RIV-tekenwisselingen, drie getekende LAT/WEL/GHB, FLF-splitsing, 2 runs met cache-hergebruik.
- `python test_server.py`: PASS, 36 synthetische MetaSWAP-decades, bronselectie, tekenconversie, checkpoint.
- `python -m py_compile build_modflow_svat.py`: PASS.
- `unzip -t ...v06_16_FLUXEN.zip`: OK.

**Geen echte NHI-serverrun van v0.6 geverifieerd.** Controle op juistheid van bron-IDF-dekking en tijdreeksen volgt na terugkoppeling server.
