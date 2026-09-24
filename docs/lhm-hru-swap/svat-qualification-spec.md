# SVAT qualification specification

Status: **DRAFT AUTHORITY**

Dit document definieert hoe plausibiliteitsanalyse, correcties en gebruiksbesluiten voor SVATs worden vastgelegd. Het doel is onderzoek mogelijk te maken zonder beslissingen te verbergen in losse batchfiles of handmatig gewijzigde CSV's.

## 1. Drie begrippen die niet mogen worden samengevoegd

### Observation

Een geconstateerd patroon of potentieel probleem, bijvoorbeeld extreem hoge kwel.

### Qualification rule

Een reproduceerbare regel die bepaalt welke SVATs voor nader onderzoek worden gemarkeerd.

### Usage policy

De beslissing wat downstream met een gemarkeerde SVAT gebeurt.

Een qualification rule mag dus nooit impliciet betekenen "vervang deze waarde".

## 2. Regeldefinitie

Iedere regel krijgt minimaal:

- rule_id;
- versie;
- korte naam;
- betrokken variabelen;
- exacte vergelijking;
- eenheden;
- periode/tijdsbetekenis;
- landgebruik-/gebiedsvoorwaarden;
- uitzonderingsgebieden;
- inhoudelijke motivatie;
- datum;
- auteur/eigenaar;
- code/configuratiecommit;
- status: EXPERIMENTAL, CANDIDATE of CANONICAL.

Voorbeeld van de vorm, niet van een te bevriezen criterium:

    rule_id: KWEL_HIGH
    expression: netto_kwel > threshold
    threshold: <config>
    unit: mm/day
    exceptions: <config>

Drempels staan in configuratie, niet verborgen in programmabroncode.

## 3. Output per SVAT

Per regel wordt een afzonderlijke flag opgeslagen:

- 0: regel niet geraakt;
- 1: regel geraakt;
- NA: regel niet evalueerbaar.

Daarnaast kan een samengestelde samenvatting worden gemaakt, maar die vervangt nooit de afzonderlijke flags.

## 4. Correcties

Een echte inhoudelijke correctie wordt apart geregistreerd.

Minimale correctietabel:

| veld | betekenis |
|---|---|
| svat_id | doel-SVAT |
| variable | gecorrigeerde variabele |
| source_value | oorspronkelijke waarde |
| corrected_value | nieuwe waarde |
| unit | eenheid |
| correction_id | type correctie |
| reason | inhoudelijke motivatie |
| config_version | gebruikte regels/configuratie |
| code_commit | producerende code |
| run_id | run waarin de correctie is toegepast |

De bronwaarde blijft in SVAT_BASE beschikbaar.

## 5. Gebruiksbesluit

Voor iedere relevante downstream toepassing wordt de policy expliciet vastgelegd.

Minimaal:

- use_for_hru_clustering;
- use_for_hru_hydrology;
- use_for_swap_meteorology;
- use_for_swap_groundwater_boundary;
- use_for_swap_drainage;
- replacement_policy, indien van toepassing.

Deze flags hoeven niet identiek te zijn. Een SVAT kan bijvoorbeeld ongeschikt zijn voor een specifieke randvoorwaarde maar nog wel bruikbaar zijn voor een bodem- of landgebruiksclassificatie.

## 6. Vervanging en donorrelaties

Wanneer een waarde of SVAT wordt vervangen, moet dat een expliciet product zijn.

Minimaal:

- target_svat;
- donor_svat of replacement_method;
- betrokken variabele(n);
- reden;
- voorwaarde waaronder de donor geldig is;
- afstand/kwaliteitsmaat indien relevant;
- gebruikte configuratie;
- run-id.

Donortoewijzing vanuit HRU-clustering en vervanging vanwege hydrologische onwaarschijnlijkheid worden als verschillende relaties opgeslagen.

## 7. Onderzoek naar een nieuwe fout

Wanneer downstream QA een nieuw patroon ontdekt:

1. registreer het als observatie;
2. kwantificeer omvang en ruimtelijk patroon;
3. ontwikkel een regel op een onderzoeksbranch/configuratie;
4. bereken welke SVATs door de regel worden geraakt;
5. test effect op HRU/SWAP;
6. vergelijk met de vorige canonical run;
7. accepteer, wijzig of verwerp;
8. alleen bij acceptatie krijgt de regel CANONICAL status.

Een onderzoeksvondst verandert dus nooit direct een canonical dataset.

## 8. Rapportage per wijziging

Iedere wijziging van een kwalificatieregel rapporteert minimaal:

- aantal geraakte SVATs oud/nieuw;
- geraakt oppervlak oud/nieuw;
- overlap en verschilset;
- ruimtelijke kaart;
- effect op relevante hydrologische statistieken;
- effect op HRU-toewijzing indien relevant;
- effect op SWAP-QA indien relevant.

Dit maakt inhoudelijke discussie over drempels of uitzonderingen controleerbaar.
