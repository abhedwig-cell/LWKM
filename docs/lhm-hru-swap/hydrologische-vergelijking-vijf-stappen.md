# Hydrologische vergelijking in vijf stappen

Status: **CONCEPT AUTHORITY**

## Doel

De kernvraag is niet alleen of de uiteindelijke HRU-representatie voldoende goed is, maar vooral **welke bewerkingsstap welke hydrologische verandering veroorzaakt**.

Voor de huidige LWKM 2.0-lijn onderscheiden we daarom vijf direct vergelijkbare toestanden. Een puur technische ruimtelijke afbakening wordt daarbij gescheiden van de inhoudelijk relevante selectie van landbouw en natuur.

## De vijf toestanden

### S0 — SVAT Nederland basis

Populatie:
- oorspronkelijke LHM/SVAT-hydrologie;
- buitenlandse cellen verwijderd;
- grote/open oppervlaktewateren en andere niet-relevante ballast buiten het Nederlandse modeldomein verwijderd;
- **nog geen selectie op landbouw en natuur**;
- nog geen Flevoland-correctie;
- nog geen behandeling van hydrologische extremen.

Doelbestand:

`SVAT_NL_BASE.csv`

Dit is de hydrologische referentie voor Nederland na alleen de afgesproken technische afbakening.

### S1 — SVAT landbouw + natuur

De hydrologische waarden zijn gelijk aan S0, maar de populatie wordt beperkt tot het LWKM-domein van landbouw en natuur.

Doelbestand:

`SVAT_LBN.csv`

Vergelijking:

`S1 - S0` = **effect van de selectie landbouw + natuur**.

Dit effect is inhoudelijk relevant en moet expliciet zichtbaar worden gemaakt. Het is dus geen technische ballastverwijdering.

### S2 — SVAT + Flevoland-correctie

Dezelfde SVAT-sleutels, hetzelfde schema en hetzelfde domein als S1.

Alleen de geaccepteerde hydrologische correctie voor Flevoland wordt toegepast.

Doelbestand:

`SVAT_FLEVOLAND_CORR.csv`

De correctie kan uit meer bestaan dan alleen kwel als uit de alternatieve LHM-run blijkt dat ook gekoppelde ontwaterings-, drainage- of andere balanscomponenten mee moeten veranderen.

Vergelijking:

`S2 - S1` = **effect van de Flevoland-correctie**.

### S3 — SVAT + behandeling van extremen

Dezelfde SVAT-sleutels, hetzelfde schema en hetzelfde domein als S2.

Hydrologisch onwaarschijnlijke of extreme SVAT-waarden worden behandeld volgens een expliciet en versieerbaar beleid. Als waarden via een donor of andere SVAT worden vervangen, worden doel-SVAT, bron-SVAT en vervangen variabelen expliciet vastgelegd.

Doelbestand:

`SVAT_QUALIFIED_REP.csv`

Vergelijking:

`S3 - S2` = **effect van de behandeling van extremen**.

Dit effect mag de Flevoland-correctie niet meer bevatten, omdat die al in S2 is toegepast.

### S4 — HRU10242-representatie

De HRU-afleiding wordt gebaseerd op S3.

Benodigde producten:
- `SVAT_HRU_MAP.csv`;
- `HRU_SCHEMA.csv`;
- HRU-niveau hydrologische representatie.

Voor een zuivere één-op-één vergelijking met S3 worden de HRU-waarden teruggeprojecteerd op het oorspronkelijke SVAT-domein:

`SVAT → HRU → HRU-waarde terugzetten op iedere bijbehorende SVAT`.

Doelbestand:

`SVAT_HRU10242_BACKPROJECTED.csv`

Dit bestand bevat dezelfde SVAT-sleutels en vergelijkbare hydrologische kolommen als S3.

Vergelijking:

`S4_backprojected - S3` = **zuiver effect van de HRU-representatie**.

Dit is de maat waarmee zichtbaar kan worden gemaakt hoeveel hydrologische informatie verandert of verloren gaat bij de reductie van ruim 400.000 SVATs naar circa 10.000 HRU's.

## Waarom terugprojecteren naar SVAT-niveau belangrijk is

Een landelijk HRU-totaal kan er goed uitzien terwijl lokale positieve en negatieve afwijkingen elkaar compenseren.

Door de HRU-representatie terug te projecteren naar iedere oorspronkelijke SVAT-locatie krijgen S3 en S4:

- dezelfde ruimtelijke ondersteuning;
- dezelfde SVAT-sleutels;
- dezelfde oppervlakteweging.

Daardoor kunnen we:

- landelijke waterbalansen vergelijken;
- regionale waterbalansen vergelijken;
- kaarten van lokale afwijkingen maken;
- verdelingen van absolute en relatieve fouten bepalen;
- regio's aanwijzen waar de HRU-representatie mogelijk onvoldoende is.

## Te rapporteren effecten

Voor iedere overgang wordt apart gerapporteerd:

1. **S0 → S1:** selectie landbouw + natuur;
2. **S1 → S2:** Flevoland-correctie;
3. **S2 → S3:** behandeling van hydrologische extremen;
4. **S3 → S4:** HRU-representatie.

Per relevante waterbalansvariabele worden minimaal bepaald:

- gebiedsgewogen landelijk totaal of gemiddelde vóór en na;
- absoluut verschil;
- relatief verschil;
- MAE;
- RMSE;
- P01, P50 en P99 van lokale verschillen;
- maximale absolute afwijking;
- beïnvloed oppervlak;
- regionale samenvattingen;
- ruimtelijke kaart van de verandering.

## Toerekening van veranderingen

De effecten worden **incrementeel** bepaald en niet cumulatief door elkaar gehaald.

Conceptueel:

```text
totale verandering S0 → S4
  =
  effect selectie landbouw+natuur  (S0 → S1)
+ effect Flevoland-correctie        (S1 → S2)
+ effect extremenbeleid             (S2 → S3)
+ effect HRU-representatie          (S3 → S4)
```

Voor optelbare waterbalanscomponenten moet deze decompositie, op afrondingsverschillen en expliciet gedocumenteerde niet-lineaire transformaties na, numeriek sluiten.

## Regionale analyse

Landelijke gemiddelden zijn niet voldoende.

Iedere vergelijking moet daarom ook kunnen worden uitgesplitst naar een stabiele regionale indeling, bijvoorbeeld:

- waterbeheergebied;
- LHM-district;
- provincie;
- landbouwgebied;
- andere afgesproken rapportagegebieden.

De gebruikte regionale indeling moet voor alle vijf toestanden identiek en versieerbaar zijn.

Doel daarvan is zichtbaar maken:

- waar landelijke effecten ruimtelijk geconcentreerd zijn;
- waar positieve en negatieve afwijkingen elkaar landelijk compenseren;
- waar HRU-representatie lokaal mogelijk onvoldoende is.

## Communicatie richting Deltares

De analyse moet duidelijk onderscheid maken tussen:

**Correcties en selectie van LHM-brondata**
- selectie landbouw + natuur;
- Flevoland-correctie;
- behandeling van hydrologisch onwaarschijnlijke/extreme LHM-resultaten.

en:

**LWKM-schematisatie-effect**
- HRU-aggregatie en HRU-representatie.

De belangrijkste boodschap is daarom niet alleen het uiteindelijke verschil tussen LHM en HRU, maar juist de toerekening:

> Welk deel van de uiteindelijke verandering komt door selectie en correctie van de LHM-brondata, en welk deel ontstaat door de reductie van de ruimtelijke representatie naar HRU's?

## Minimale gegevensbehoefte

De analyse kan zuiver worden uitgevoerd wanneer deze vijf vergelijkbare producten beschikbaar zijn:

1. `SVAT_NL_BASE.csv`
2. `SVAT_LBN.csv`
3. `SVAT_FLEVOLAND_CORR.csv`
4. `SVAT_QUALIFIED_REP.csv`
5. `SVAT_HRU10242_BACKPROJECTED.csv`

Alle vijf moeten dezelfde afspraken gebruiken voor:

- SVAT-sleutel;
- domein;
- kolomnamen;
- eenheden;
- periode;
- oppervlaktebasis.

De afzonderlijke `SVAT_HRU_MAP` en `HRU_SCHEMA` blijven daarnaast nodig als provenanceproducten voor stap S4.
