# Reconstructie invoer HRU10242 uit exact aangeleverde CSV-bestanden

**Datum:** 28 september 2026  
**Status:** brongebonden reconstructie

## 1. Bestanden en checksums

Aangeleverd en direct geïnspecteerd:

- `SVAT_INFO.csv`
  - 552.705 rijen
  - 58 kolommen
  - SHA-256: `5f7b657508a4dc885bd60fae93051239046b27788388d6e8832621eaa85fe192`
- `svat_info_lwkm_new.csv`
  - 427.656 rijen
  - 59 kolommen
  - SHA-256: `5ea4d24a0ce38c802cb1dbf63e30239664965438fbcc55690acced447a248821`
- `xyLDGBclus.csv`
  - 560.887 rijen
  - 4 kolommen
  - SHA-256: `c659530fb69e32af5fe309b7ae80e20b470e88094b92569f851a32321182d21e`

## 2. Domeinselectie

In `SVAT_INFO.csv`:

- `islwkm=1`: **427.656 SVATs**
- `islwkm=0`: **125.049 SVATs**

De set van 427.656 SVAT-id's met `islwkm=1` is **exact gelijk** aan de set SVAT-id's in `svat_info_lwkm_new.csv`.

Daarmee is voor de feitelijke HRU10242-input hard vastgesteld:

```text
SVAT_INFO.csv
    │
    └─ filter islwkm == 1
           ↓
       427.656 SVATs
```

Let op: dit specifieke `SVAT_INFO.csv` bevat 552.705 rijen en wijkt daarmee af van een eerder gedeelde oudere SVAT_INFO-variant met een ander totaal. Voor de HRU10242-reconstructie is de nu aangeleverde file met bovenstaande checksum de relevante bron.

## 3. Wat is `svat_info_lwkm_new.csv` precies?

De nieuwe tabel bevat één extra kolom:

`svat_donor`.

Voor **20.934 SVATs** geldt:

`svat_donor != svat`.

Voor exact dezelfde 20.934 SVAT-id's geldt in de oorspronkelijke geselecteerde `SVAT_INFO.csv`:

minimaal één van:

- `ghg_sel`
- `gt1_sel`
- `gt2_sel`
- `gt8_sel`
- `kwel_sel`
- `wegzijging_sel`
- `runoff_sel`
- `subinfil_sel`

is groter dan nul.

Dus:

> **De donorvervanging in `svat_info_lwkm_new.csv` is exact toegepast op de 20.934 hydrologisch geflagde SVATs.**

Er zijn in deze pre-HRU replacementstap géén extra donorwisselingen buiten de hydrologisch geflagde populatie.

Dit moet strikt worden onderscheiden van de latere HRU-koppeltabel `export_svat_HRU_NRU_10242.csv`, waarin een grotere donor/restgroeprelatie voorkomt.

## 4. Vervangingssemantiek

Voor de 20.934 vervangen SVATs zijn alle inhoudelijke gemeenschappelijke velden gecontroleerd tegen de oorspronkelijke rij van `svat_donor`.

Voor **54 inhoudelijke kolommen** geldt voor alle 20.934 vervangingen:

```text
waarde in svat_info_lwkm_new
=
waarde van svat_donor in oorspronkelijk geselecteerde SVAT_INFO
```

Dat geldt onder andere voor:

- GHG/GLG;
- neerslag/verdamping;
- runoff;
- afvoer/aanvoer;
- kwel/wegzijging;
- qlat;
- drainage;
- beregening;
- Gt;
- landgebruiksklassen;
- bodemklassen;
- hydrologische klassen;
- kwalificatieflags;
- `islwkm`;
- `isberegen`;
- `isdrain`;
- `isverdacht`.

De eigen SVAT-identiteit blijft behouden.

### Oppervlak

`opp(m2)` wordt **niet** van de donor overgenomen.

Voor alle 20.934 vervangen SVATs blijft het oppervlak gelijk aan het oppervlak van de target-SVAT.

Dit is belangrijk en logisch: de donor levert de eigenschappen, niet het vertegenwoordigde oppervlak.

### Coördinaten

De kolommen `x` en `y` in `svat_info_lwkm_new.csv` zijn exact gelijk aan de oorspronkelijke `xc(m)` en `yc(m)` van de target-SVAT.

Dus ook de geografische locatie blijft die van de target.

## 5. Effect op flags

In de oorspronkelijke geselecteerde SVAT-set:

- minimaal één flag: **20.934**
- `isverdacht > 0`: **20.934**

In `svat_info_lwkm_new.csv`:

- alle acht afzonderlijke flags: **0**
- `isverdacht > 0`: **0**

Dit komt doordat de inhoudelijke donorwaarden, inclusief de flagvelden, zijn overgenomen.

Voor de nieuwe canonical workflow is dit **niet gewenst als enige vastlegging**, omdat daarmee de reden waarom een target-SVAT vervangen is uit de gematerialiseerde tabel verdwijnt.

De moderne workflow moet daarom naast de effectieve waarden altijd bewaren:

- target-SVAT;
- donor-SVAT;
- oorspronkelijke flags;
- oorspronkelijke waarden;
- effectieve/vervangende waarden;
- replacement-rule-id.

## 6. Consequentie voor vijfstappenmodel

De historische keten kan nu veel preciezer worden beschreven:

```text
SVAT_INFO.csv
  552.705 SVATs
       │
       ├─ islwkm == 1
       ▼
  427.656 SVATs
       │
       ├─ 20.934 hydrologisch verdachte SVATs
       │
       ├─ donor toewijzen
       │
       └─ donor-eigenschappen kopiëren,
          target-id/locatie/oppervlak behouden
       ▼
svat_info_lwkm_new.csv
  427.656 SVATs
       │
       ▼
HRU clustering
```

Daarmee is `svat_info_lwkm_new.csv` inhoudelijk de historische gematerialiseerde vorm van de **S3 replacementstap vóór HRU-clustering**.

## 7. LDGB-koppeling

Van de 427.656 SVAT-coördinaten zijn:

- **427.631** exact aanwezig in `xyLDGBclus.csv`;
- **25** hebben geen exacte x/y-match.

Voor alle 25 ontbrekende matches ligt de dichtstbijzijnde LDGB-locatie exact **250 m** verderop.

Dit bevestigt dat de nearest-neighbour fallback in het R-script daadwerkelijk relevant is, maar slechts voor 25 SVATs in deze dataset.

## 8. Belangrijke methodologische correctie op eerdere reconstructie

Eerder was op basis van de latere HRU-koppeltabel zichtbaar dat 57.880 SVATs een andere `svat_donor` hebben.

Met de nu aangeleverde echte HRU-input is duidelijk geworden dat dit twee verschillende donorconcepten zijn:

### Pre-HRU replacement

In `svat_info_lwkm_new.csv`:

- 20.934 donorwisselingen;
- exact de hydrologisch geflagde SVATs.

### HRU clustering/restgroep donor

In `export_svat_HRU_NRU_10242.csv`:

- bredere donorrelatie;
- bevat ook donor-matching door HRU-clustering/restgroepbehandeling.

Deze relaties mogen in documentatie, code en QA nooit meer onder dezelfde betekenis `svat_donor` worden samengevoegd.

Aanbevolen canonical namen:

- `replacement_donor_svat`;
- `hru_cluster_donor_svat`;
- `hru_representative_svat`.

## 9. Wat hiermee gesloten is

Met deze drie bestanden zijn nu sterk of volledig gebonden:

- feitelijke HRU10242 SVAT-basisset;
- exacte islwkm-selectie voor deze run;
- omvang van de verdachte populatie;
- relatie tussen flags en pre-HRU replacement;
- inhoudelijke semantiek van `svat_info_lwkm_new.csv`;
- target versus donor eigendom van oppervlak en locatie;
- LDGB nearest-neighbour fallback.

## 10. Wat nog open blijft

Nog nodig voor volledige reproductie van HRU10242:

1. het script/de methode waarmee de `svat_donor` voor de 20.934 verdachte SVATs is gekozen;
2. exact vastleggen welke ruleset de acht flags produceerde;
3. HRU-R-script opnieuw draaien met deze exact gebonden inputs;
4. bewijzen dat dezelfde 10.242 HRU's worden gereproduceerd;
5. koppelen van de geproduceerde timestamp-bestanden aan de huidige `export_*_10242.csv`.

