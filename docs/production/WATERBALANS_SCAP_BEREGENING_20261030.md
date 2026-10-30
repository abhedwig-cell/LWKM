# LWKM waterbalans: besluit 2026-10-30, grondwaterberegening uit scap_svat.inp

Scope: MODFLOW-laag 1, MetaSWAP apart en gecombineerde balans. Volledige verwerking 1970–2022, klimaatgemiddelde 1991–2020. BDGQLAT wordt uit dagelijkse FRF/FFF gemaakt conform BBC09; MetaSWAP heeft decadische IDF's bdgqmodf, bdgetact, bdgqrun, bdgdecstot, bdgPm, bdgPssw en bdgPsgw.

## Gecontroleerd invoerbestand
Gebruiker leverde op 2026-10-30 `scap_svat(1).inp`, 57.937 regels. Het laatste veld legt de MODFLOW-onttrekkingslaag voor grondwaterberegening vast. De verdeling over dit laatste veld is:

| Laag | SVAT's |
| ---: | ---: |
| 0 | 21619 |
| 1 | 1 |
| 2 | 19 |
| 3 | 5202 |
| 4 | 10917 |
| 5 | 5382 |
| 6 | 9394 |
| 7 | 2481 |
| 8 | 2922 |
| **Totaal** | **57937** |

Enige SVAT met laag 1: **207543**. Laag 0 betekent vooralsnog *niet bewezen* 'geen beregening': toets dit aan oorspronkelijke invoerdefinitie. De aanwezige waarde `25.00` is nog niet semantisch vastgesteld. Aantal SVAT's per laag zegt niet hoeveel water daadwerkelijk onttrokken wordt.

## Gecombineerde balans: beslisregel
- `bdgPsgw` van een SVAT met toegewezen onttrekkingslaag **1**: binnen het beschouwde MetaSWAP + MODFLOW-laag-1-systeem interne verplaatsing. Alleen laten wegvallen tegen de *aantoonbaar corresponderende* negatieve laag-1-WEL-onttrekking. Verschillen afzonderlijk zichtbaar houden.
- `bdgPsgw` vanuit laag **2 of dieper**: toevoer van buiten de gecombineerde laag-1-systeembalans.
- `laag 0`: niet automatisch in een van bovenstaande categorieën opnemen zonder originele velddefinitie.
- Vergelijk beregeningsvolumes en WEL met gelijke SVAT-/celondersteuning en tijdsinterval; leg verschillen apart vast. Geen automatische correctie van balansresten.
- `bdgPssw` is externe watertoevoer vanuit oppervlaktewater voor dit afgebakende systeem, tenzij een andere expliciet meegenomen systeemgrens dat verandert.

## Nog te verifiëren
1. Oorspronkelijke betekenis van alle SCAP-kolommen en laag 0.
2. Of WEL per dag de aan laag 1 toegewezen beregeningsonttrekking daadwerkelijk bevat, inclusief ruimtelijke en temporele toerekening.
3. Tekenconventies en tijdssemantiek van MetaSWAP-decaden vóór afleiding van de balansrest.
4. MODFLOW-berging ontbreekt: de gecombineerde fluxrest mag niet automatisch fout worden genoemd.
