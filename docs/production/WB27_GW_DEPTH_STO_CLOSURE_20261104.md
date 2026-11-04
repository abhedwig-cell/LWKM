# WB27: grondwaterdiepte en STO-balansklassen, januari 2020

Datum: 4 november 2026. Status: **diagnostiek afgerond; geen automatische STO-toewijzing toegelaten**.

## Bron en uitvoering
Gebaseerd op daadwerkelijk op de NHI-server uitgevoerde WB27-proef, resultaatarchief `uitvoer_WB27.zip`: `status.json`, `summary_by_class.csv`, `depth_by_class_and_coverage.csv`, `depth_matched_2_vs_4.csv`, `source_inventory.json` en per-SVAT profielscenario's. `status=COMPLETED_HYPOTHESIS_TEST_NOT_CAUSAL_PROOF`, 645574 SVATs; geen verworpen `area_svat`-regels. Dag-IDF's laag 1 van 10, 20, 31 januari 2020 (samengevoegde head-rasters; géén losse partities). Deze drie momentopnamen zijn **geen echt maandgemiddelde**.

`glk` afkomstig uit oorspronkelijke `area_svat.inp`; de ware profielonderkant `dpbotk` is **niet bekend**. Dieptescenario's 3, 5, 10 meter zijn gevoeligheidstoetsen, niet de werkelijke MetaSWAP-profielgrenzen.

## Gevalideerde uitkomsten
| Balansklasse | N | Mediane grondwaterdiepte (m) | Aandeel >10m |
|---|---:|---:|---:|
| 1 alleen zonder MODFLOW-STO | 586838 | 0.961709 | 0.017978 |
| 2 alleen met MODFLOW-STO | 47029 | 31.188026 | 0.999809 |
| 3 beide | 6590 | 0.813402 | 0.010926 |
| 4 geen van beide | 5117 | 15.551261 | 0.584131 |

Klasse 2 hangt uitzonderlijk sterk samen met diepe grondwaterstand. Klasse 4 omvat zowel natte als diepe situaties; de grondwaterdiepte alleen verklaart klasse 4 niet. Binnen 88 gecombineerde strata van 10km, diepteklasse en celdekking bevinden zich voldoende cases van klasse 2 én 4, zodat diepte niet gelijkgesteld kan worden aan een beslisregel.

## Broncode-evidence
In door gebruiker aangeleverde `msw1postfm.for`, `msw1postfm_sc1` (regels 268-288), wordt de waterbergingscoëfficiënt anders berekend indien MODFLOW-grondwaterstand `lvgwmodf <= glk - dpbotk + dc`. Dit betreft de **MetaSWAP-profielonderkant**, niet MODFLOW `BOT_l1`. Met de huidige bestanden is de causale relatie niet aantoonbaar.

Dezelfde Fortran-bron definieert in `msw1postfm_qmodf` (regels 118-135) `qmodf` via opslag- en overige koppelfluxen als een afgeleide restterm. `qmodf` niet opnemen als onafhankelijke SWAP/HRU-waterbalansflux.

## Projecteigenaarbesluit en werkafbakening
- WB27 onderzoek afsluiten; geen verdere STO-regimezoektocht vóór productie HRU-keten.
- Geen STO fysisch uitsluiten; geen automatische per-SVAT switch op grond van optimale rest, grondwaterdiepte of geografische ligging.
- Scheid hydrologische externe flux, interne gekoppelde uitwisseling en verzadigde/onverzadigde berging, voorkom dubbeltelling.
- Januari/februari geven goede numerieke sluiting voor grootste deel SVATs, maar niet automatisch volledige fysische systeemsluiting.
- Resterende 5117 SVATs in klasse 4 blijven gemarkeerd als open uitzonderingen; ze blokkeren niet automatisch onafhankelijke HRU-randvoorwaardereconstructies.
- **Vervolg LWKM**: prioriteit herstellen op HRU-productieketen, dagelijkse laag-1-QEXT vanuit de originele FLF+FRF+FFF+GHB+WEL (reeds gereconstrueerd), oppervlaktewatersystemen en SWAP-inputs; sluiting diagnostisch houden.

## Herleidbaarheid
Serverresultaat `uitvoer_WB27.zip`, 4 november 2026, door projecteigenaar geüpload. Originele bronwaarden zijn niet gewijzigd. Voor reproductie van de volledige uitkomst moet originele serverinvoer (area_svat, head) en classificatie uit WB23/26 behouden blijven.
