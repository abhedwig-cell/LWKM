# WB07: ruimtelijke MetaSWAP qmodf / MODFLOW klimaatfluxdiagnose

Datum: 2026-11-03. Software geleverd als ZIP in de bijbehorende ChatGPT-sessie; deze commit documenteert de methode, **niet** een reeds uitgevoerde nationale serverrun.

## Bronnen

- WB06 `MF_L1_QEXT4_YYYYMM_Dk.IDF` (1080 decades 1991–2020), met QLAT + **ongecorrigeerde** FLF + WEL + GHB. Brontekens blijven onveranderd.
- Originele `E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp`, oorspronkelijke 645.582 SVATs, veld 2 oppervlakte en velden 10/11 X/Y (1-gebaseerd).
- Oorspronkelijke MODFLOW `E:\LHM_4.3.3\Data\2_Model_Input\modflow\bnd\ibound_l1.idf`.
- Decadische `bdgqmodf`-IDF's met datum = 10e, 20e, maandultimo en het projectcontract m3/m2 per decade.

## Rekenwijze en grenzen

1. Controleer 1080 WB06-hashes en de vaste kalenderdecades.
2. Lees alle originele SVAT-oppervlakten en X/Y, map naar hun MODFLOW-cel. Behoud meerdere SVATs per cel en selecteer exact de unieke gekoppelde MODFLOW-cellen.
3. Per decade: `sum(SVAT_area * BDGQMODF_depth)` (m3) versus `sum(WB06_QEXT4 on matched MODFLOW cells)`.
4. Bewaar landelijke volumes, zowel som als verschil met ongewijzigde tekens, de oppervlakte-dekking, SHA's en controles op ruimtelijke uitlijning.
5. Geen stilzwijgende NoData=0; bij onvolledige SVAT-dekking geen schijnbaar volledig MetaSWAP-totaal.

**Wetenschappelijke beperking:** WB06 heeft slechts vier MODFLOW-termen. Directe gelijkheid van QEXT4 en qmodf is niet bewezen of geëist; dit is nog geen sluitende gecombineerde balans. De gekwalificeerde 2020–2022-laag-1-sluiting gebruikt ook DRN, RIV, BND en STO (WB04/WB05). MetaSWAP qdr=0 in deze toepassing, en SVAT 207543 is de mogelijke laag-1-onttrekkingsuitzondering voor qspgw. Vergelijking op HRU-niveau volgt na exacte koppeling met de HRU-support.

## Uitvoeringsstatus

Synthetische lokale eerste-decade-proef en syntaxcontrole geslaagd. Echte 1991–2020-IDF-lezing, timing, eenheden/tekens, volledigheid en fysieke interpretatie nog door de server te verifiëren.
