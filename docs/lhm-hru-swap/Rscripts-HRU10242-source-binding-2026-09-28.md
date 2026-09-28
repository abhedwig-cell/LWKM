# Inventarisatie R-scripts en binding HRU10242

**Datum:** 28 september 2026  
**Bron:** aangeleverde `Rscripts.zip`

## Belangrijkste vondst

Het feitelijke bronbestand:

`Rscripts/HRU_clustering/HRU_clustering_LWKM20_31082026.R`

is aanwezig in de aangeleverde ZIP.

SHA-256 van deze bron:

`6e5055241590be6bf7f7afe53a2eaf3f03ab3e0627cb9a82bbae138b73eb599e`

Hiermee is het belangrijkste eerdere authority-gat rond de actuele HRU10242-bron gesloten. De resterende stap is reproductie van de huidige 10.242-HRU output uit exact gebonden inputbestanden.

## Brongebonden parameters

Uit de broncode:

- `MinOppha = 500 ha`;
- `groupfraction = 0.25`;
- `MAE_threshold_GHG = 1000`;
- `MAE_threshold_Nkw = 500`;
- `minnosvats = 10`;
- `minsvatsinNRU = 4`;
- `reduction_factor = 0.841`;
- `FlagClus = TRUE`.

Voor `LDGBclus` 35, 38 en 56 gelden kleinere minima:

- `minnosvats = 4`;
- `minsvatsinNRU = 2`.

## Exact geobserveerde invoer

De bron gebruikt projectroot:

`w:/PROJECTS/ESG_DB_PROJECTS/Waterkwaliteitsmodellen/Ontwikkeling LWKM2.0/Vaststellen HRUs/`

en leest:

- `Herschikking/20251114/svat_info_lwkm_new.csv`;
- `Herschikking/20251114/SVAT_INFO.csv`;
- `xyLDGBclus.csv`.

De eerste is de primaire clusterinput.

SVATs waarvoor in de primaire input:

`svat_donor != svat`

worden uit die primaire dataset gehaald en vervolgens opnieuw opgebouwd uit het oorspronkelijke `SVAT_INFO.csv`, gefilterd op `islwkm == 1`.

Dit bevestigt het eerder benoemde risico: de HRU-afleiding combineert feitelijk twee SVAT-toestanden. Daarom moet `svat_info_lwkm_new.csv` nu exact worden gereconstrueerd en moet worden vastgesteld welke correcties daarin al zijn verwerkt.

## Belangrijke bronlogica

- ontbrekende LDGB-koppelingen worden via nearest neighbour op x/y aangevuld;
- oppervlakte wordt op 6,25 ha per SVAT gezet;
- `isdrain` wordt geforceerd op 0 voor `lu2 == 2`;
- clusteringvariabelen zijn `GHG_LHM43` en `NettoKwel_LHM43`;
- er zijn 11 aggregatie-/versoepelingsrondes;
- targets buiten geaccepteerde clusters worden via gewogen nearest-neighbour aan donoren gekoppeld;
- iedere HRU krijgt een werkelijk bestaande representatieve SVAT;
- de centrale representatieve SVAT wordt bepaald als medoid op GHG en NettoKwel;
- aanvullende representatieve punten worden op p10/p90-combinaties bepaald.

## Concrete source bug / aandachtspunt

De bron schrijft eerst het HRU-raster naar:

`Result/HRU_LWKM20_<timestamp>.asc`

en schrijft direct daarna het NRU-raster naar **dezelfde bestandsnaam**.

Daarmee kan het NRU-raster het HRU-raster overschrijven.

Dit moet in de gemoderniseerde workflow worden opgelost door verschillende expliciete productnamen.

## Andere relevante bestanden in de ZIP

De ZIP bevat ook:

- oudere HRU-clusteringsversies;
- gerefactorde varianten;
- geoptimaliseerde varianten;
- losse helperfuncties;
- Shiny-viewer scripts.

Deze zijn nuttig als ontwikkelhistorie, maar worden niet automatisch production-authority. De bron `HRU_clustering_LWKM20_31082026.R` blijft voor de huidige HRU10242-reconstructie de primaire referentie.

## Nog nodig voor volledige reproductie

1. producer en checksum van `Herschikking/20251114/svat_info_lwkm_new.csv`;
2. checksum/versie van `Herschikking/20251114/SVAT_INFO.csv`;
3. checksum/versie van `xyLDGBclus.csv`;
4. identificeren welke timestamp-output overeenkomt met de huidige `export_*_10242.csv` bestanden;
5. de bron opnieuw uitvoeren en bewijzen dat dezelfde 10.242 HRU's worden geproduceerd.
