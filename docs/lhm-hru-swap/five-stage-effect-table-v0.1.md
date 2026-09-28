# Vijfstappen-effecttabel v0.1

**Datum:** 28 september 2026  
**Status:** eerste concrete effecttabel uit reeds gedeelde data

Deze tabel scheidt de effecten zo ver mogelijk op basis van de huidige gedeelde bestanden. Waar de brondata nog niet voldoende is om een effect zuiver toe te rekenen, staat dat expliciet vermeld.

| overgang | effect | huidig concreet resultaat | status |
|---|---|---|---|
| S0 → S1 | selectie naar huidig LWKM-domein | 552.834 → 427.656 SVATs; 125.178 SVATs vallen buiten de huidige selectie | **gereconstrueerd**, semantische binding van S0/S1 nog formaliseren |
| S1 → S2 | Flevoland hydrologische correctie | zichtbaar in `kwel_org → kwel` bij 4.677 SVATs, circa 268,0 km² | **gedeeltelijk gekwantificeerd** |
| S1 → S2 | effect op gebiedsgemiddelde kwel | 116,93 → 108,67 mm/j; delta -8,26 mm/j | **diagnostisch** |
| S1 → S2 | volumetrisch kwel-effect | circa -210,7 miljoen m³/jaar over huidig geselecteerd domein | **diagnostisch** |
| S2 → S3 | minimaal één hydrologische kwalificatieflag | 20.934 SVATs, circa 1.226,6 km² | **gereconstrueerd** |
| S2 → S3 | daadwerkelijke replacement | nog niet zuiver gelijk te stellen aan flags | **open** |
| S3 → S4 | donor-SVAT verschilt van eigen SVAT | 57.880 SVATs | **gereconstrueerd, maar niet zuiver HRU-verlies** |
| S3 → S4 | donorwissel én hydrologisch geflagd | 20.934 SVATs | **gereconstrueerd** |
| S3 → S4 | donorwissel zonder huidige hydrologische flag | 36.946 SVATs | **gereconstrueerd** |
| S4 | actuele ruimtelijke reductie | 427.656 SVATs → 10.242 HRU's → 25.054 NRU's | **gereconstrueerd** |
| S3 → S4 | hydrologisch informatieverlies op GHG/NettoKwel | terugprojectie-script nu ingericht; numerieke uitvoering nog nodig | **klaar voor uitvoering** |

## Kwalificatieflags

| regel | SVATs | oppervlak |
|---|---:|---:|
| `ghg_sel` | 2.243 | 126,7 km² |
| `gt1_sel` | 1.803 | 106,0 km² |
| `gt2_sel` | 2.069 | 124,6 km² |
| `gt8_sel` | 3.629 | 208,4 km² |
| `kwel_sel` | 8.622 | 511,7 km² |
| `wegzijging_sel` | 3.934 | 230,3 km² |
| `runoff_sel` | 2.280 | 136,5 km² |
| `subinfil_sel` | 979 | 51,6 km² |
| **uniek, minimaal één regel** | **20.934** | **1.226,6 km²** |

De som van de afzonderlijke regels is groter dan de unieke populatie omdat regels overlappen.

## Interpretatie

### 1. Domeinselectie is een afzonderlijk effect

De huidige geselecteerde keten gebruikt 427.656 van de 552.834 SVATs uit de gereconstrueerde bredere basis. Dit moet als eigen hydrologische stap worden gerapporteerd, niet als administratieve filtering.

### 2. Flevoland is landelijk zichtbaar

Hoewel de cellen waarin `kwel_org` en `kwel` verschillen slechts circa 268 km² beslaan, is het effect op het gebiedsgemiddelde van de huidige selectie circa -8,26 mm/j. Daarmee is bevestigd waarom deze lokale correctie ook in landelijke balansen zichtbaar kan zijn.

Dit blijft voorlopig een **kweldiagnose**. De gekoppelde ontwaterings-/drainagecomponenten moeten nog aan dezelfde correctie worden gebonden voordat S1 → S2 als volledige hydrologische correctie wordt gesloten.

### 3. Flags en donorwisselingen zijn niet hetzelfde

De huidige data laten een zeer duidelijk onderscheid zien:

- hydrologisch geflagd: **20.934 SVATs**;
- donorwissel: **57.880 SVATs**.

Alle huidige geflagde SVATs vallen binnen de donorwisselgroep, maar daarnaast zijn er **36.946 niet-geflagde SVATs** die eveneens een donor krijgen.

Daarom moet de nieuwe workflow twee aparte mechanismen modelleren:

1. hydrologisch kwaliteits-/extremenbeleid;
2. HRU-restgroep en donor-/representatiebeleid.

### 4. Het pure HRU-effect moet via backprojection worden bepaald

Een donorwissel is niet hetzelfde als hydrologisch informatieverlies door HRU-aggregatie.

Het pure effect wordt daarom berekend als:

`S3 SVAT-waarde → HRU-gemiddelde → terugprojectie naar dezelfde SVAT`.

Voor GHG en NettoKwel is de QA-code hiervoor nu uitgebreid. Daarmee kunnen per SVAT, regio en landelijk niveau MAE, RMSE, percentielen en extrema worden bepaald zodra de actuele CSV's uitvoerbaar beschikbaar zijn.

## Nieuwe QA-uitvoer

`tools/qa_lhm_hru_swap.py` produceert na de uitbreiding ook:

- `qualification_overlap.csv`: overlapmatrix van de acht kennisregels;
- uitgebreid `hru_mapping_summary.csv`: flags versus donorwisselingen;
- `hru_average_backprojection.csv`: zuivere SVAT → HRU-gemiddelde terugprojectie wanneer de kolommapping is gebonden.

