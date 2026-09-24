# LWKM-WORKFLOW01 — reproduceerbare dataflow en incrementele modelinvoer

Status: **PROJECTBASELINE**
Datum: 2026-09-24
Scope: LWKM dataverwerking, ruimtelijke selectie en toekomstige SWAP-invoergeneratie

## Besluit

LWKM legt de inhoudelijke bewerking vast, niet de toevallige historische software waarmee die bewerking eerder is uitgevoerd.

Legacy Fortran-programma's, scripts en andere hulpmiddelen zijn daarom niet automatisch onderdeel van de nieuwe productiearchitectuur. Zij kunnen drie rollen hebben:

1. **wetenschappelijk model** — behouden zolang de modelinhoud daar thuishoort;
2. **referentie/oracle** — bevroren gebruiken om nieuw gedrag tegen te vergelijken;
3. **historisch hulpmiddel** — vervangen zodra de inhoudelijke regels expliciet zijn gereconstrueerd en gekwalificeerd.

Een letterlijke vertaling van legacy-code naar Python is geen doel. Eerst wordt vastgesteld welke bronnen, selecties, transformaties, regels en aggregaties de inhoudelijke methode vormen. Daarna wordt die methode opnieuw implementeerbaar en testbaar gemaakt.

## Technische uitgangspunten

De voorlopige voorkeursarchitectuur is:

- Python als primaire taal voor databewerking, selectie, analyse en orkestratie;
- GeoParquet voor tabulaire/vectoriële ruimtelijke tussenresultaten waar passend;
- xarray met NetCDF en/of Zarr voor raster-, tijdreeks- en meerdimensionale gegevens waar passend;
- QGIS voor inspectie en visuele controle, niet als ongeregistreerde productiestap;
- notebooks alleen voor exploratie, diagnose en onderzoek; productielogica verhuist naar gewone code en tests;
- GitHub voor code, configuratie, documentatie en qualification evidence;
- een workflowmanager zoals Snakemake kan worden ingevoerd zodra de inhoudelijke keten voldoende stabiel is. De workflowmanager is geen voorwaarde om met het inhoudelijke werk te starten.

Toolkeuzes blijven vervangbaar zolang interfaces, provenance en resultaten behouden blijven.

## Dataflow is expliciet

Een bewerking wordt vastgelegd als opeenvolging van betekenisvolle toestanden en transformaties. Bijvoorbeeld:

bron Nederland
→ geharmoniseerd Nederland
→ relevant Nederlands analysedomein
→ Natuur-Nederland
→ analyse-eenheden
→ indicatoren
→ aggregaties/eindresultaten

De overgang van het relevante Nederlandse analysedomein naar **Natuur-Nederland** is een inhoudelijke selectie en mag niet als onzichtbare filterstap verdwijnen.

Voor deze overgang wordt standaard evidence gemaakt van ten minste:

- oppervlak vóór selectie;
- oppervlak na selectie;
- uitgesloten oppervlak;
- verdeling naar relevante categorieën;
- ruimtelijke controle van uitgesloten en behouden delen;
- effect van de selectie op relevante vervolgvariabelen, waar dat inhoudelijk betekenisvol is.

Ook eerdere domeinfilters, zoals uitsluiting van buitenland en niet-relevante grote/buitendijkse oppervlaktewateren, worden expliciet benoemd en reproduceerbaar uitgevoerd.

## Artefacttypen

De workflow maakt onderscheid tussen:

### 1. Scientific result
De inhoudelijke uitkomst die voor analyse of modellering wordt gebruikt.

### 2. Diagnostic evidence
Tussenresultaten, oppervlaktes, verschillen, balanscontroles, oracle-vergelijkingen en andere informatie die nodig is om te begrijpen en kwalificeren hoe het resultaat tot stand kwam.

### 3. Presentation product
Kaarten, tabellen, spreadsheets, figuren en rapportages. Deze zijn afgeleid en zijn niet zelf de inhoudelijke authority.

## Kleine functies, geen nieuwe monoliet

De nieuwe keten wordt opgebouwd uit kleine, expliciete bewerkingen met duidelijke input en output, bijvoorbeeld:

- read_source
- harmonise
- define_analysis_domain
- select_nature
- map_parameters
- calculate_indicator
- aggregate
- compare_with_reference

De precieze API staat nog niet vast. Het principe wel: één groot nieuw LWKM-programma waarin alle bewerkingen opnieuw verborgen raken is niet het doel.

## Provenance per officiële run

Een officiële run krijgt een machineleesbaar manifest met ten minste:

- run-id;
- datum/tijd;
- Git commit of softwareversie;
- gebruikte configuratie;
- bronbestanden en waar mogelijk inhoudshashes;
- relevante selectieregels;
- softwareomgeving;
- aantallen/oppervlakken per belangrijke selectiestap;
- waarschuwingen;
- resultaatbestanden en waar mogelijk inhoudshashes.

Doel is dat achteraf kan worden vastgesteld welke inhoudelijke bronnen en regels een resultaat hebben geproduceerd.

# LWKM-SWAP-INPUT

De bestaande keten voor het maken van SWAP-invoer bestaat uit legacy Fortran en aanvullende scripts, waaronder scripts waarmee uiteindelijk echte **SWP-bestanden** worden gemaakt. Deze keten wordt op termijn vervangen.

## Hoofdprincipe

Een SWP-bestand is een **model-specifiek exportproduct**, niet de primaire inhoudelijke opslag van de configuratie.

De nieuwe keten wordt conceptueel:

landelijke brondata
→ normalisatie en koppelingen
→ parameter authority
→ modelneutrale SWAP-configuratie per rekeneenheid
→ change/dependency detection
→ SWP-export en overige benodigde SWAP-invoer
→ simulatie

Hierdoor worden inhoudelijke modelconfiguratie en de concrete SWAP-bestandssyntaxis van elkaar gescheiden.

## Incrementele generatie

De invoergenerator moet niet standaard alle rekeneenheden opnieuw genereren.

Iedere rekeneenheid krijgt een stabiele identificatie en expliciete afhankelijkheden van relevante bronnen en parameters. De generator moet kunnen bepalen of de inhoudelijke configuratie sinds een eerdere build is veranderd.

Gewenst gedrag:

- ongewijzigde configuratie → geen nieuwe SWP-generatie nodig;
- wijziging die slechts een subset raakt → alleen die subset opnieuw genereren;
- handmatige selectie van een subset moet mogelijk blijven;
- dezelfde inhoudelijke invoer moet deterministisch dezelfde modelinvoer opleveren.

Een inhoudelijke hash/fingerprint van de effectieve configuratie is de voorkeursrichting voor change detection. Alleen timestamps zijn onvoldoende authority.

## Selectieve aansturing

De toekomstige aansturing moet conceptueel ten minste ondersteunen:

- volledige build;
- expliciete lijst van rekeneenheden;
- selectie volgens een inhoudelijk criterium of gebied;
- alleen rekeneenheden waarvan de effectieve invoer sinds een vorige build is gewijzigd.

De precieze command-line-interface wordt later bepaald.

## Reconciliatie vóór herschrijven

De huidige Fortran + scripts-keten wordt niet direct herschreven. Eerst wordt zij ontleed in:

1. gebruikte bronnen;
2. transformaties en beslisregels;
3. afgeleide parameters;
4. koppelingen tussen bestanden/eenheden;
5. uiteindelijke SWP-semantiek;
6. andere vereiste SWAP-invoerbestanden;
7. performancekenmerken;
8. een representatieve frozen set bestaande outputs als oracle.

Pas daarna wordt een nieuwe generator geïmplementeerd.

## Qualification

De vervangende SWAP-invoergenerator moet minimaal worden getoetst op:

- inhoudelijke gelijkheid of verklaarde verschillen ten opzichte van de legacy-oracle;
- determinisme;
- correcte dependency-selectie;
- geen onnodige rebuild van ongewijzigde eenheden;
- reproduceerbare provenance;
- performance voor representatieve batches, bijvoorbeeld 100, 1000 en de volledige orde van grootte van circa 10.000 rekeneenheden;
- expliciete verklaring van verschillen in gegenereerde SWP-bestanden.

Performancewinst is gewenst, maar inhoudelijke correctheid en traceerbaarheid gaan voor.

## Nieuwe werkstromen

### LWKM-DATAFLOW
Bouw de reproduceerbare keten van brondata via analysedomein en Natuur-Nederland naar analyse-eenheden, indicatoren en aggregaties. Begin met een kleine echte keten en gebruik die als architectuurproef.

### LWKM-SWAP-INPUT
Reconcilieer eerst de bestaande Fortran + scripts-invoergenerator. Bouw daarna een modelneutrale configuratielaag en een incrementele SWP-exporter.

## Eerstvolgende uitvoerbare stap

Voor **LWKM-DATAFLOW** wordt één echte bestaande ruimtelijke keten volledig gereconstrueerd en reproduceerbaar gemaakt, inclusief de expliciete overgang van Nederlands analysedomein naar Natuur-Nederland.

Voor **LWKM-SWAP-INPUT** wordt nog niet herschreven. De eerste werkunit inventariseert de bestaande Fortran-programma's, vervolgscripts, bronbestanden, afgeleide producten, afhankelijkheden en runtime, en legt een representatieve bestaande SWP-set vast als oracle.
