# Concrete reconstructie huidige LWKM-keten uit reeds gedeelde data

**Datum:** 28 september 2026  
**Status:** reconstructie op basis van reeds gedeelde archieven en bronbestanden  
**Doel:** de vijfstappenvergelijking zo ver mogelijk concreet invullen zonder nog ontbrekende authority-bewijzen te verzinnen.

## 1. Samenvatting

Met de reeds gedeelde bestanden kan de huidige keten aanzienlijk verder worden ingevuld dan alleen op architectuurniveau.

De belangrijkste concrete bevindingen zijn:

- het oudere aangeleverde `SVAT_INFO.CSV` bevat **552.834 SVATs**;
- daarvan hebben **427.656 SVATs** `islwkm=1`;
- exact diezelfde **427.656 SVAT-id's** komen terug in de huidige `SVAT_INFO_HRU.CSV` en in `export_svat_HRU_NRU_10242.csv`;
- de huidige geselecteerde SVAT-populatie beslaat volgens `opp(m2)` circa **25.511 km²**;
- in de huidige SVAT-tabel wijkt `kwel(mm/j)` bij **4.677 SVATs** af van `kwel_org(mm/j)`;
- die 4.677 SVATs beslaan circa **268 km²** en liggen ruimtelijk in een begrenzing die sterk overeenkomt met Flevoland;
- op de volledige geselecteerde SVAT-populatie daalt het oppervlaktegewogen gemiddelde van `kwel_org` van circa **116,93 mm/j** naar **108,67 mm/j** in `kwel`;
- dat is een verschil van circa **-8,26 mm/j**, oftewel **-7,06%**, overeenkomend met circa **-210,7 miljoen m³/jaar** over het geselecteerde domein;
- **20.934 SVATs** hebben minimaal één van de acht huidige kwalificatieflags;
- deze flags beslaan samen circa **1.227 km²**;
- alle 20.934 geflagde SVATs krijgen in de huidige HRU-koppeltabel een andere donor-SVAT;
- in totaal krijgen echter **57.880 SVATs** een andere donor-SVAT;
- daarvan zijn dus **36.946 SVATs niet geflagd** door de huidige acht kwalificatieregels;
- de huidige HRU-koppeltabel bevat **427.656 SVATs → 10.242 HRU's**;
- het actuele NRU-schema bevat **25.054 NRU's**.

Dit betekent dat drie verschillende processen die historisch gemakkelijk door elkaar kunnen lopen nu numeriek van elkaar kunnen worden onderscheiden:

1. domeinselectie;
2. Flevoland-correctie;
3. hydrologische flags versus bredere HRU-donor-/restgroepbehandeling.

## 2. S0 → S1: Nederland naar LWKM-domein

### Beschikbare bron

Het aangeleverde oudere bestand:

`LHM2SWAP/LHM4.3 data 2024/SVAT_INFO.CSV`

bevat:

- totaal: **552.834 SVATs**;
- `islwkm=1`: **427.656 SVATs**;
- `islwkm=0`: **125.178 SVATs**.

De set met `islwkm=1` heeft exact dezelfde SVAT-id's als de huidige 427.656 regels in:

- `SVAT_INFO_HRU.CSV`;
- `export_svat_HRU_NRU_10242.csv`.

### Betekenis

Hiermee kan de overgang naar het huidige LWKM-domein technisch al worden gereconstrueerd.

Er wordt **22,6% van de SVAT-records** uit de 552.834-record basis niet meegenomen in de huidige LWKM-selectie.

### Nog niet volledig bewezen

Voor de definitieve vijfstappenrapportage moet nog expliciet worden bewezen dat:

- deze 552.834 SVATs precies de bedoelde `SVAT_NL_BASE` vormen;
- `islwkm=1` semantisch exact overeenkomt met de afgesproken selectie landbouw + natuur na technische verwijdering van buitenland/open water.

De identieke SVAT-id-set maakt dit wel een zeer sterke reconstructiekandidaat.

## 3. S1 → S2: Flevoland-correctie

De huidige `SVAT_INFO_HRU.CSV` bevat zowel:

- `kwel_org(mm/j)`;
- `kwel(mm/j)`.

Dit maakt voor kwel een directe diagnostische reconstructie mogelijk.

### Gevonden verschil

Aantal SVATs waarbij beide kolommen verschillen:

**4.677**

Oppervlak van deze SVATs:

**268,0 km²**

Aandeel van de huidige geselecteerde oppervlakte:

**1,05%**

Ruimtelijke begrenzing van de gewijzigde cellen:

- x: circa **138.375 – 197.625 m**
- y: circa **475.375 – 538.875 m**

Deze ligging is sterk consistent met Flevoland. De formele correctiemasker-authority moet echter nog worden gebonden voordat dit als definitieve bewijsvoering wordt gebruikt.

### Effect op kwel

Over het volledige huidige geselecteerde domein:

| grootheid | oorspronkelijke kolom | gebruikte/gecorrigeerde kolom |
|---|---:|---:|
| oppervlaktegewogen kwel | 116,93 mm/j | 108,67 mm/j |
| verschil |  | **-8,26 mm/j** |
| relatief verschil |  | **-7,06%** |

Het volumetrische verschil over het geselecteerde domein bedraagt circa:

**-210,7 miljoen m³/jaar**

Binnen alleen de gewijzigde cellen is de oppervlaktegewogen gemiddelde verandering circa:

**-785,9 mm/j**.

### Belangrijke beperking

Dit kwantificeert alleen wat zichtbaar is in `kwel_org → kwel`.

Het bewijst nog niet dat daarmee de **volledige Flevoland hydrologische correctie** correct is gereconstrueerd. Zoals eerder vastgesteld kunnen ook ontwaterings-, drainage- of andere balanscomponenten mee moeten veranderen.

Voor formele S1 → S2-admission moet daarom de alternatieve LHM-run en de volledige set mee gewijzigde balanscomponenten worden gebonden.

## 4. S2 → S3: hydrologische kwalificatie

De huidige `SVAT_INFO_HRU.CSV` bevat acht afzonderlijke kwalificatievelden.

| flag | aantal SVATs | oppervlak |
|---|---:|---:|
| `ghg_sel` | 2.243 | 126,7 km² |
| `gt1_sel` | 1.803 | 106,0 km² |
| `gt2_sel` | 2.069 | 124,6 km² |
| `gt8_sel` | 3.629 | 208,4 km² |
| `kwel_sel` | 8.622 | 511,7 km² |
| `wegzijging_sel` | 3.934 | 230,3 km² |
| `runoff_sel` | 2.280 | 136,5 km² |
| `subinfil_sel` | 979 | 51,6 km² |

Omdat flags overlappen, is de som groter dan de unieke populatie.

Uniek geflagd door minimaal één regel:

- **20.934 SVATs**
- circa **1.226,6 km²**

Het samengestelde veld `isverdacht` is bij exact dezelfde 20.934 SVATs ongelijk aan nul.

### Wat hiermee al kan

We kunnen nu reproduceerbaar rapporteren:

- hoeveel SVATs iedere regel raakt;
- hoeveel oppervlak iedere regel raakt;
- waar de flags ruimtelijk liggen;
- welke regels overlappen;
- welke hydrologische kenmerken de geflagde populatie heeft.

### Wat nog ontbreekt

Een flag is nog niet hetzelfde als een vervanging.

De definitieve S2 → S3-transformatie vereist een expliciete policy:

- welke flag leidt tot uitsluiten;
- welke flag leidt tot vervangen;
- welke variabele wordt vervangen;
- door welke donor/bronwaarde;
- welke uitzonderingen gelden.

## 5. Historische donor-/vervangingslaag

De huidige `export_svat_HRU_NRU_10242.csv` bevat een `svat_donor`.

Aantal SVATs waarvoor:

`svat_donor != svat_orig`

is:

**57.880**

Daarvan:

- **20.934** zijn ook hydrologisch geflagd;
- **36.946** zijn niet geflagd door de acht huidige kwalificatieregels.

Dit is een belangrijk resultaat.

Het betekent dat de huidige donorbehandeling **breder is dan alleen het vervangen van hydrologische extremen**.

De HRU-documentatie laat zien dat ook SVATs uit te kleine/onvoldoende clusters naar donor-matching kunnen gaan.

Daarom mag de huidige donorrelatie niet zonder meer worden geïnterpreteerd als:

> “dit zijn de 57.880 hydrologisch onbetrouwbare SVATs”.

Dat zou onjuist zijn.

### Koppeling met reeds gedeeld analysebestand

In het aangeleverde:

`LHM2SWAP/analyses/svat_cor.csv`

blijken exact dezelfde **57.880 SVAT-id's** ten opzichte van `svat.csv` op minimaal één inhoudelijk veld te veranderen.

Dit maakt `svat_cor.csv` een zeer sterke kandidaat voor een historisch gematerialiseerde donor-/replacementweergave.

Maar omdat deze 57.880 zowel hydrologische flags als HRU-restgroep/donormatching omvatten, is dit **niet automatisch de zuivere S3-extremencorrectie** die we nu willen definiëren.

## 6. S4: actuele HRU10242

De huidige bestanden zijn concreet:

### `export_svat_HRU_NRU_10242.csv`

- regels: **427.656**
- unieke HRU's: **10.242**

### `export_HRUschema_10242.csv`

- HRU's: **10.242**
- bevat per HRU onder andere:
  - aantal SVATs;
  - klassekenmerken;
  - gemiddelde/mediaan/standaardafwijking GHG;
  - gemiddelde/mediaan/standaardafwijking NettoKwel;
  - MAE en RMSE voor GHG;
  - MAE en RMSE voor NettoKwel;
  - scheefheid;
  - representatieve SVAT;
  - vier aanvullende p10/p90-representatieve SVATs.

### `export_NRUschema_10242.csv`

- NRU's: **25.054**

Daarmee is S4 op dit moment verreweg de best ingevulde stap.

## 7. Wat al direct kan worden teruggeprojecteerd

De mapping bevat voor iedere SVAT:

- eigen GHG;
- eigen NettoKwel;
- HRU-id.

Het HRU-schema bevat:

- `GHG_average`;
- `NettoKwel_average`.

Daarmee kan zonder aanvullende brondata het HRU-gemiddelde terug op iedere SVAT worden geprojecteerd:

`SVAT → HRU → HRU-average`.

Daaruit kunnen direct worden gemaakt:

- `delta_GHG_HRU = GHG_average(HRU) - GHG_orig(SVAT)`;
- `delta_NettoKwel_HRU = NettoKwel_average(HRU) - NettoKwel_orig(SVAT)`;
- landelijke MAE/RMSE;
- regionale MAE/RMSE;
- verschilkaarten;
- percentielen;
- oppervlak boven gekozen foutgrenzen.

De bronbestanden bevatten bovendien al HRU-specifieke MAE/RMSE-indicatoren. De nieuwe analyse moet deze bestaande diagnostiek hergebruiken en uitbreiden, niet opnieuw uitvinden.

## 8. Huidige vijfstappenstatus

| toestand | concreet beschikbare reconstructie | status |
|---|---|---|
| **S0 SVAT_NL_BASE** | 552.834 SVATs in oudere `SVAT_INFO.CSV` | sterke kandidaat, formele domeinsemantiek nog binden |
| **S1 SVAT_LBN** | exact 427.656 SVATs via `islwkm=1`; zelfde id-set als actuele keten | zeer sterke kandidaat |
| **S2 SVAT_FLEVOLAND_CORR** | voor kwel: 4.677 gewijzigde SVATs, 268 km², -210,7 Mm³/j | kwel-effect concreet; volledige balanscorrectie nog open |
| **S3 SVAT_QUALIFIED_REP** | 20.934 geflagde SVATs, 1.226,6 km²; historische donorlaag 57.880 | flags concreet; replacement-policy nog niet zuiver gebonden |
| **S4 HRU10242** | 427.656 SVATs → 10.242 HRU's; 25.054 NRU's | zeer concreet, producerende R-run nog formeel binden |

## 9. Belangrijkste nieuwe inhoudelijke conclusie

De reeds gedeelde data laten zien dat de keten waarschijnlijk **niet** simpelweg bestaat uit:

`extremen markeren → precies die extremen vervangen → HRU maken`.

Er zijn namelijk:

- 20.934 hydrologisch geflagde SVATs;
- maar 57.880 SVATs met een andere HRU-donor.

Dus minimaal twee mechanismen spelen door elkaar:

1. hydrologische kwalificatie/extremen;
2. HRU-clustering/restgroep/donormatching.

Voor de nieuwe canonical workflow moeten deze mechanismen expliciet worden losgekoppeld.

Dat is essentieel om later richting Deltares zuiver te kunnen zeggen hoeveel verandering voortkomt uit:

- broncorrectie;
- hydrologisch kwaliteitsbeleid;
- en daadwerkelijke HRU-aggregatie.

## 10. Eerstvolgende numerieke acties

De volgende analyses kunnen nu rechtstreeks op de huidige bestanden worden uitgevoerd:

1. vijfstappentabel aanvullen met landelijke waterbalanscomponenten;
2. overlapmatrix van de acht kwalificatieflags;
3. kaart/selectiebestand van de 4.677 `kwel_org != kwel`-SVATs;
4. verschil tussen alleen geflagde replacement en volledige 57.880-donorlaag;
5. HRU-backprojection voor GHG en NettoKwel;
6. regionale effecttabellen;
7. controle of de 4.677 kwelcorrectiecellen exact overeenkomen met het formele Flevoland-correctiemasker;
8. koppeling van ontwaterings-/drainagecorrecties aan dezelfde Flevoland-cellen.

