# Frank v08: donorprofielen voor verdachte SVATs

## Aanleiding en besluitruimte

Na de v07 LWKM-selectie en Flevolandcorrectie vroeg de projecteigenaar om de
eerder als verdacht aangemerkte cellen te behandelen. Op 23 november 2026 gaf
de eigenaar opdracht hiervoor logische keuzes te maken. Deze notitie legt de
nieuwe toepassingsregel voor de huidige 49 Frankkolommen vast. De eerder
gereproduceerde selectie en donoridentiteiten blijven het uitgangspunt.

De implementatie staat in [tools/frank_verdacht_v08](../../tools/frank_verdacht_v08).
Het complete Windows-pakket heet `LWKM_Frank_Verdachte_SVATs_v08.zip` en bevat
ook de gekwalificeerde gecomprimeerde koppeltabellen. De code gebruikt de
Python-standaardbibliotheek. Er is geen database, nieuwe LHM-run of herlezing
van de dag-IDFs en decade-heads.

## Selectie en donor

De acht oorspronkelijke kwalificatieflags selecteren precies 20.934 van de
427.656 LWKM-SVATs. Voor elk van deze targets wordt de operationele
`hru_cluster_donor_svat` gebruikt. De overige 36.946 niet-zelfdonorrelaties
veroorzaken geen vervanging, omdat deze targets niet oorspronkelijk verdacht
zijn. De oudere `legacy_pre_hru_donor_svat` en de HRU-representant hebben
andere rollen.

De nieuwe compacte donortabel is opgebouwd uit de gehashte historische
membership en de oorspronkelijke flags. Alle donoren bestaan, horen bij
dezelfde HRU, zijn niet verdacht en zijn zelfdonor. De OR van de acht flags
is exact gelijk aan de 20.934 IDs met oorspronkelijke `isverdacht != 0`.
De selectie wordt niet opnieuw uit de nieuwe Frankgetallen afgeleid.

## Nieuwe regel per kolom

Bij een verdachte target worden de 35 hydrologische kolommen 13 t/m 47 als
een volledig profiel overgenomen uit de ongewijzigde donorrij van dezelfde
bronvariant. Het gaat om Gt, GLG/GHG/GG/dynamiek, de twee echte
decadepercentielen, kwelklasse, alle watertermen inclusief neerslag en
beregening, QModF, MetaSWAP-berging en beide bestaande balansdiagnostieken.
Er worden geen target- en donorwatertermen gemengd.

SVAT-ID, N, werkelijk targetoppervlak, de negen landgebruik- en bodemvelden,
gebied, positie en HRU-koppeling blijven targetgegevens. Positieve eindige
oppervlakken boven 62.500 m2 blijven ongewijzigd geldig. Ontbrekende
donorwaarden blijven leeg. Een ontbrekende donor is een koppelingsfout en
wordt niet vervangen door een willekeurige andere bron.

De intensiteiten in mm/jaar worden letterlijk overgenomen. Een volume-
equivalent wordt berekend met `mm/jaar * targetoppervlak / 1000`. Dit is
geen oorspronkelijk lokaal MODFLOW-volume. GLG/GHG en percentielen blijven
donorkengetallen in m-mv; zij zijn niet opnieuw berekend voor het target.
De overgenomen balansdiagnostiek wordt niet op nul gezet en bewijst geen
nieuwe fysische balanssluiting.

De voorlaatste indicator is 1 bij een uitgevoerde vervanging, ook als de
profielwaarden toevallig gelijk zijn. Voor andere targets blijft de eerdere
Flevolandindicator behouden. De audit onderscheidt de eerdere targetstatus,
de Flevolandstatus van het gebruikte donorprofiel en de vervanging zelf.

## HRU-samenvatting

Beide nieuwe SVAT-varianten krijgen een HRU-tabel. Alle oorspronkelijke
targetleden tellen mee, gewogen met hun actuele MetaSWAP-oppervlak. N en
oppervlak blijven gelijk. Het resultaat beschrijft daardoor het volledige
LWKM-oppervlak met toegepaste donorprofielen.

Dit is een andere toepassingsregel dan de P12 donor-equal-selectie voor
directe hydrologische aggregatie. De P12-bronleden en hun oppervlakte worden
wel als controlegegevens vermeld, maar vormen hier geen noemer. Er wordt
niet opnieuw geclusterd en er worden geen nieuwe HRU-representanten gekozen.

De negen vaste HRU-categorieën komen uit de bestaande, gehashte v07-HRU-tabel.
Gt en kwelklasse tonen de unieke actuele ledenklassen, gescheiden door `|`.
Continue kenmerken zijn gewogen SVAT-samenvattingen. HRU-percentielen zijn
geen percentielen die opnieuw uit een HRU-tijdreeks zijn berekend.

## Uitvoering en herkomst

`START_FRANK_VERDACHT` leest standaard de vier voltooide v07-tabellen en hun
manifest uit `frank_export_eindtabel/svat_lwkm_hru_v07`. Het schrijft vier
nieuwe tabellen naar `frank_export_eindtabel/svat_lwkm_hru_verdacht_v08`.
Alle tabellen behouden de 49 kolommen, komma als scheidingsteken en punt als
decimaalteken.

De bronmanifesthashes, exacte v07-membership- en schemahashes, donorbronhashes
en codehashes worden gebonden. Output wordt pas gepubliceerd nadat beide
varianten zijn voltooid en de bronbestanden opnieuw zijn gecontroleerd.
Een herstart controleert de bestaande uitvoerbytes. De methode en Windows-
instructies staan in `LEESMIJ.txt` en `METHODE_EN_KEUZES.txt` naast de code.

De gecomprimeerde dataproducten zijn opgenomen in het leverbare ZIP-pakket,
niet opnieuw als grote gegenereerde kopieën in Git. `data/SOURCES.json` en
`data/DONOR_SOURCES.json` bevatten hun hashes. Beide bouwscripts en de
instructies in `broncode/LEESMIJ_BOUW.txt` maken herbouw uit de exact gebonden
bronbestanden mogelijk.

## Verificatie en grenzen

De lokale suite bevat 53 geslaagde tests, waaronder elf integratie- en
publicatietests. Die behandelen ongelijke en grote oppervlakken, de juiste
Flevolandbronvariant, ontbrekende waarden, behoud van bronbytes, herstart,
gewijzigde bronnen en opruiming na een schrijffout. De volledige referentie
met 427.656 SVATs en 10.242 HRUs is ingelezen en gecontroleerd.

Een aparte Windows-CI-job controleert dezelfde suite op Python 3.8 en 3.12.
De status daarvan is de actuele workflow-uitvoer. Een volledige uitvoering
met de v07-serverresultaten is hiermee niet geclaimd.

## Eerdere bronnen

- [Work B-reconstructie](WORK_B_20261019.md).
- [Verdachte SVATs en operationele donoren](../lhm-hru-swap/SUSPECT-SVAT-DONOR-RECONCILIATION-2026-09-30.md).
- [Eigenaarschap donorrelaties](../lhm-hru-swap/donor-relations-ownership-2026-09-28.md).
- [P12 donorselectie](../lhm-hru-swap/P12-DONOR-SELECTION-CORRECTION-CONTRACT.md).

