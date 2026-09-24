# Data products and contracts

Status: **DRAFT AUTHORITY**

Deze specificatie beschrijft de productgrenzen van de canonical workflow. Het doel is dat iedere stap afzonderlijk kan worden gewijzigd, getest en vervangen.

## LHM_EXPORT

### Rol

Afgesproken overdracht van de NHI/LHM-omgeving naar de LWKM-omgeving.

### Verplicht

- manifest;
- bron-LHM-versie;
- periode per variabele;
- eenheid;
- oppervlaktebasis;
- ruimtelijke referentie;
- bronbestand;
- checksum;
- producerend script/configuratie.

## SVAT_BASE

### Sleutel

Eén stabiele SVAT-ID per rij.

### Verplicht

- x/y of andere ruimtelijke sleutel;
- oppervlak;
- landgebruik;
- bodem;
- GHG/GLG;
- noodzakelijke waterbalanscomponenten;
- bron/provenance per variabele of variabelegroep.

Bronwaarden worden niet destructief gewijzigd.

## SVAT_QUALIFIED

### Sleutel

SVAT-ID, 1-op-1 met SVAT_BASE.

### Toevoegingen

- domeinflags;
- correctiewaarden en correctie-id;
- qualification-rule flags;
- usage-policy flags;
- eventuele replacement/donorrelaties als aparte tabel.

SVAT_QUALIFIED is geen fysiek verkleinde subset. Downstream views mogen wel selecties maken.

## SVAT_HRU_MAP

### Sleutel

SVAT-ID.

### Verplicht

- HRU-ID;
- indien relevant NRU-ID;
- clustering-/matchingroute;
- donorrelatie voor clustering;
- aggregatieronde;
- kwaliteitsinformatie die nodig is om de toewijzing te begrijpen.

## HRU_SCHEMA

### Sleutel

HRU-ID.

### Verplicht

- classificerende HRU-kenmerken;
- representatieve SVAT(s);
- GHG/NettoKwel-statistiek indien onderdeel van de methode;
- relevante kwaliteitsmaten;
- totale oppervlakte;
- methode/configuratieversie.

## SWAP_MAPPING

Geen dataset met resultaten maar een versieerbare wetenschappelijke specificatie.

Per SWAP-invoerveld:

| eigenschap | verplicht |
|---|---|
| target SWAP field | ja |
| bronproduct + kolom | ja |
| selectie/usage policy | ja |
| aggregatiefunctie | ja |
| weging | ja |
| eenheidsconversie | ja |
| tekenconventie | ja |
| tijdsondersteuning | ja |
| fallback | indien van toepassing |

## SWAP_INPUT

Per run:

- run-id;
- HRU-ID;
- alle SWAP-invoerbestanden;
- gegenereerd uit vastgelegde SWAP_MAPPING;
- checksum per bestand;
- producerende codecommit.

## SWAP_OUTPUT_QA

Minimaal:

- runstatus per HRU;
- waterbalans;
- relevante hydrologische output;
- QA-flags;
- vergelijking met gekozen LHM/SVAT-referentie;
- onderscheid tussen representatie-effect en modeleffect waar mogelijk.

## ANIMO_HANDOFF

Dit is het eindproduct van deze workflow.

De inhoud wordt samen met de ANIMO-eigenaar vastgelegd, maar de verdere ANIMO-verwerking valt buiten scope.

## Bestandsformaten

CSV, SQLite, rasters en SWAP-native invoer kunnen naast elkaar bestaan. Het format is ondergeschikt aan het datacontract.

Een canonical product moet altijd:

- machineleesbaar zijn;
- schema en eenheden hebben;
- stabiele sleutels gebruiken;
- gekoppeld zijn aan een runmanifest;
- niet afhankelijk zijn van impliciete bestandsvolgorde of lokale absolute paden.
