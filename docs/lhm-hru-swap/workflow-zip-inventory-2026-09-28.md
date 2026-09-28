# Inventarisatie LWKM_workflow_no_asc.zip

**Datum:** 28 september 2026  
**Status:** eerste inhoudelijke reconstructie uit aangeleverde workflow-ZIP

## 1. Omvang

De aangeleverde ZIP bevat 2.078 entries.

Belangrijkste bestandstypen:

- 1.921 CSV-bestanden;
- 110 IDF-bestanden;
- 15 logbestanden;
- 10 PAR-bestanden;
- 9 BAT-bestanden;
- 2 INP-bestanden;
- 1 geneste ZIP;
- diverse kleine lookup- en diagnostiekbestanden.

De ZIP bevat daarmee veel meer dan strikt nodig, maar juist genoeg om een groot deel van de historische producerende keten te reconstrueren.

## 2. Belangrijkste teruggevonden workflow-bestanden

### Batchbestanden

Teruggevonden zijn onder andere:

- `do_gridcalc_lgn.bat` — versie/timestamp 16 april 2026;
- meerdere varianten van `do_gridcalc_filter.bat`;
- meerdere varianten van `do_gridcalc_filter_2011-2020.bat`;
- `do_gridcalc_flf.bat`;
- `do_gridcalc.bat`.

De actuele `do_gridcalc_lgn.bat` gebruikt:

`set exedir=g:\lhm433\exe`

en:

`set per=1991-2020`.

Hij roept onder andere aan:

- `gridcalc.exe`;
- `grid_adjust.exe`;
- `grid2class.exe`;
- `grid2table.exe`;
- `grid2scale.exe`;
- `LWKM_makeHRU.exe`.

De batch bevat dus daadwerkelijk een groot deel van de producerende logica tussen LHM-grids en de SVAT/HRU-input.

## 3. Grondwatertrap wordt expliciet opgebouwd

De actuele batch reconstrueert `gt.asc` via tussenbestanden:

- `glg50.asc`;
- `glg80.asc`;
- `glg120.asc`;
- `ghg40.asc`;
- `ghg80.asc`;
- `ghg140.asc`;
- `ghg4080.asc`;
- `ghg80140.asc`;
- `gt1.asc` t/m `gt8.asc`.

Daarna:

`gt1 + gt2 + ... + gt8`

wordt gecombineerd tot `gt.asc`.

Dit is precies het type tijdelijke gridketen dat in de gemoderniseerde workflow niet meer als losse permanente tussenbestanden hoeft te bestaan. De logica kan rechtstreeks als versieerbare transformatie worden geïmplementeerd.

## 4. Verdachte-cellenregels zijn grotendeels teruggevonden

De batch bevat zowel oudere selectielogica als het expliciete blok:

`REM afspraken okt-25`.

Daarin zijn de regels voor:

- subinfiltratie;
- runoff landbouw/natuur;
- wegzijging;
- kwel landbouw/natuur;
- droge Gt + kwel;
- GHG boven maaiveld

zichtbaar.

Daarnaast bestaan oudere/aanvullende routes via:

- `glg_sel`;
- `gt1_sel`;
- `gt2_sel`;
- `gt8_sel`;
- `dynamiek_sel`;
- `piet_sel`;
- `verdachte_cellen`;
- `verdachte_cellen_extra`;
- `verdachte_cellen_extreem`;
- `verdachte_cellen_old`;
- `combi_sel_*.asc`.

Dit bevestigt dat de huidige workflow historisch meerdere generaties van kennisregels bevat die in dezelfde batch zijn blijven staan. Modernisering moet deze eerst classificeren als ACTIVE / SUPERSEDED / DIAGNOSTIC voordat er één canonical ruleset wordt gemaakt.

## 5. Lookup-tabellen zijn aanwezig

Relevante lookup-/classificatietabellen in de ZIP zijn onder meer:

- `flux2class.csv`;
- `gxg2class.csv`;
- `dyn2class.csv`;
- `roff2class.csv`;
- `ontw2class.csv`;
- `kwelflux2class.csv`;
- `lu2lwkm.csv`;
- `lgn2lu2.csv`;
- `lgn2lu4.csv`;
- `ghg2fuzzy.csv`;
- `glg2fuzzy.csv`;
- `kwelmmd2fuzzy.csv`;
- `ontw2fuzzy.csv`.

### Voorbeeld: landgebruik naar LWKM

`lu2lwkm.csv` bevat expliciet een LWKM-mapping.

LWKM-ID > 0 wordt toegekend aan onder andere:

- gras;
- mais;
- akkerbouwgroepen;
- bos;
- moeras;
- natuur;
- heide;
- fruit.

LWKM-ID 0 wordt toegekend aan onder andere:

- glastuinbouw;
- water;
- stedelijk;
- sportvelden.

Deze tabel is zeer waarschijnlijk een belangrijk onderdeel van de semantiek achter het LWKM-domein en moet in de nieuwe workflow als expliciete configuratie worden opgenomen.

## 6. Filter-LWKM: veel bewijs, producer nog niet volledig gesloten

De ZIP bevat:

- `FILTER_LWKM.IDF`;
- diagnostische CSV's voor `filter_lwkm` en `filter_lwkm3`;
- meerdere batchbestanden die `filter_lwkm.asc` gebruiken.

Een diagnostische tabel uit oktober 2025 geeft voor `filter_lwkm`:

**427.660 cellen met waarde 1**.

Dat ligt zeer dicht bij de 427.656 actuele SVATs in de huidige HRU-keten.

Er is in `do_gridcalc_filter.bat` ook een uit-gecommentarieerde producerende regel voor `filter_lwkm3.asc`:

```text
IF(lgn250.asc IN relevante klassen) * if(avat.asc > 0) = filter_lwkm3.asc
```

maar voor het huidige `filter_lwkm.asc` is de volledige producerende authority nog niet aangetoond.

Dat betekent: **islwkm kunnen we nu bijna reconstrueren, maar nog niet canonical sluiten.**

## 7. Poldermasker

De ZIP bevat ook:

- `POLDERS.IDF`;
- diagnostische `polders_summary.csv`;
- `polders_table.csv`.

De tabel bevat 3.180 gemarkeerde rastercellen, circa 198,75 km² bij 250 m cellen.

Dit is genoeg om het masker technisch mee te nemen, maar nog niet om de inhoudelijke herkomst/definitie van dit masker te documenteren.

## 8. Belangrijke observatie over historische batchfiles

De actuele `do_gridcalc_lgn.bat` bevat tegelijk:

- oude selectieregels;
- nieuwe oktober-2025-regels;
- gecommentarieerde regels;
- experimentele/diagnostische combinaties;
- meerdere varianten van `verdachte_cellen`.

Dit bevestigt de noodzaak om de workflow niet letterlijk 1-op-1 als nieuw script te kopiëren.

De reconstructie moet eerst de feitelijk actieve productielijn isoleren. Daarna kan die worden gemoderniseerd naar een declaratieve, geteste workflow zonder overbodige tussenbestanden.

## 9. Wat nu nog echt nodig is

Na inspectie van deze ZIP zijn de belangrijkste ontbrekende stukken sterk teruggebracht.

### A. Exacte actuele `control_mkHRU.inp`

De batch roept aan:

`LWKM_makeHRU.exe LWKM_makeHRU.log ..\..\control_mkHRU.inp`

maar dit controlbestand zit niet in de ZIP.

Dit is nu het belangrijkste ontbrekende bestand voor de SVAT-productie, omdat het de exacte binding van alle producerende grids naar de 75-koloms SVAT-tabel bepaalt.

### B. Exacte producer van `filter_lwkm.asc` / `islwkm`

We hebben het resultaat, diagnostiek, lookup-tabellen en historische kandidaatlogica.

Wat nog ontbreekt is één bron of expliciete bevestiging van:

- welke producerende regel momenteel authority is;
- welke bronmaskers daarbij horen;
- met name de betekenis/herkomst van `avat.asc` als die huidige logica daar nog op steunt.

### C. Feitelijke HRU10242 R-bron

Nog nodig:

`HRU_clustering_LWKM20_31082026.R`

De documentatie is beschikbaar, maar de exacte productiebron nog niet.

### D. Actuele `HRUlist2SWAP` controlfile

De Fortran-bron is beschikbaar, maar voor de concrete productieketen is de feitelijk gebruikte controlfile nodig.

### E. Flevoland producer / authority

We hebben voldoende downstream bewijs om het effect te zien, en de ZIP bevat relevante fluxproducten en polderinformatie.

Nog nodig is de bron/werkwijze die exact vastlegt:

- welke alternatieve LHM-run de correctie levert;
- welk ruimtelijk masker wordt gebruikt;
- welke balanscomponenten gezamenlijk worden vervangen.

## 10. Niet nodig om nu aan te leveren

Voor de volgende reconstructiestap zijn **niet** nodig:

- alle ontbrekende ASCII-grids;
- alle grote LHM-runbestanden;
- alle diagnostische CSV's opnieuw;
- meer Fortran-bronnen.

De huidige ZIP plus de eerder aangeleverde broncode bevatten al voldoende om de tussenstappen, klasse-indelingen en kennisregels te reconstrueren.

De eerstvolgende waardevolle aanlevering is dus vooral klein en gericht:

1. `control_mkHRU.inp`;
2. de bron/regel waarmee `filter_lwkm.asc` definitief wordt geproduceerd;
3. `HRU_clustering_LWKM20_31082026.R`;
4. de actuele controlfile voor `HRUlist2SWAP`;
5. Flevoland-correctieproducer/masker/configuratie.
