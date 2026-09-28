# Reconstructie `filter_lwkm` / `islwkm`

**Datum:** 28 september 2026  
**Status:** kandidaat-canonical reconstructie

## Uitgangspunt

`filter_lwkm.asc` hoort alle SVATs te bevatten die tot **landbouw of natuur** behoren.

De eerder gevonden afwijking van vier cellen tussen een historische `filter_lwkm`-diagnostiek (427.660) en de actuele SVAT/HRU-keten (427.656) is geen extra inhoudelijke filter. Het betreft een historische fout en wordt daarom niet als workflowstap gereconstrueerd.

## Reconstructie uit reeds gedeelde data

In het aangeleverde historische `SVAT_INFO.CSV` staan 552.834 SVATs.

De velden `lu2` en `islwkm(0/1)` geven exact:

| `lu2` | aantal | `islwkm` |
|---:|---:|---:|
| 1 | 327.624 | 1 |
| 2 | 100.032 | 1 |
| 3 | 125.178 | 0 |

Daarmee geldt voor deze dataset exact:

```text
islwkm = 1  <=>  lu2 ∈ {1, 2}
islwkm = 0  <=>  lu2 = 3
```

Totaal geselecteerd:

**427.656 SVATs**

## Onderliggende landgebruiksmapping

De aangeleverde lookup `lu2lwkm.csv` maakt de inhoudelijke definitie explicieter dan alleen `lu2`.

De volgende `landgebruik22` / `LU-ID`-klassen krijgen een `LWKM-ID > 0` en worden dus geselecteerd:

- 1 gras
- 2 mais
- 3 aardappelen
- 4 bieten
- 5 granen
- 6 overige
- 7 boomteelt
- 9 boomgaard
- 10 bollen
- 11 loofbos
- 12 naaldbos
- 13 moeras
- 14 duinvegetatie
- 15 kale
- 17 natuurlijk
- 19 donker
- 20 heidevegetatie
- 21 fruitkwekerijen

Uitgesloten (`LWKM-ID = 0`):

- 8 glastuinbouw
- 16 water
- 18 stedelijk
- 22 sportvelden

De kruistabel in het historische SVAT-bestand sluit hier exact op aan: alle geselecteerde landgebruiksklassen hebben `islwkm=1`, alle vier uitgesloten klassen hebben `islwkm=0`.

## Canonical modernisering

De nieuwe workflow hoeft `filter_lwkm.asc` niet als historische tussenfile te erven.

De domeinselectie wordt rechtstreeks reproduceerbaar afgeleid:

```text
landgebruik22
    │
    ▼
lu2lwkm lookup
    │
    ▼
LWKM-ID > 0 ?
    ├─ ja  → islwkm = 1
    └─ nee → islwkm = 0
```

Een raster `filter_lwkm.asc` kan desgewenst nog als **afgeleid exportproduct** worden gemaakt voor compatibiliteit of visualisatie, maar is niet langer de inhoudelijke authority.

De authority wordt:

1. bronveld `landgebruik22`;
2. versieerbare lookup/domain-configuratie;
3. gegenereerde `islwkm`-kolom;
4. QA op aantallen en landgebruiksklassen.

## QA-regels

Voor de huidige historische baseline gelden minimaal:

- totaal SVATs in bronset: 552.834;
- geselecteerd landbouw+natuur: 427.656;
- uitgesloten: 125.178;
- geen geselecteerde SVAT met landgebruik 8, 16, 18 of 22;
- geen uitgesloten SVAT met een van de geselecteerde landgebruiksklassen;
- `lu2 ∈ {1,2}` moet equivalent zijn aan `islwkm=1`.

De historische 427.660-cell `filter_lwkm` wordt als bekende legacy-afwijking geregistreerd en niet als referentie voor de nieuwe workflow gebruikt.
