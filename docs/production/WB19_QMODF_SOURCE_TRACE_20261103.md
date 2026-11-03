# WB19: herkomst van afwijkende bdgqmodf, 3 november 2026

## Gecontroleerde echte uitvoer
De zes aangeleverde WB18-decadebestanden (januari/februari 2020) bevatten SVAT 198271 met X=149625, Y=496625 en A=12562 m2.

Per decade zijn bdgqmodf in m3: 13431.879, 13434.037, 14775.955, 13434.732, 13441.950, 12110.853. QEXT4 (QLAT+ongecorrigeerde FLF+WEL+GHB) is respectievelijk circa 756.84, 759.03, 833.52, 759.86, 767.22, 704.20 m3. Dit verschil is aanwezig in de bron-BW18-uitvoer, niet uitsluitend in de latere grote CSV-export. De qmodf-waarde is per dag vrijwel constant rond 1343–1346 m3/d.

Voor februari D1 is het qmodf-volume 13434.732 m3, versus QEXT4 circa 759.855 m3. Op basis van de bekende zeven posten is de SVAT-rest 13571.899 m3; het bij dezelfde cel horende RIV-volume is -897.069 m3. Noch RIV, noch toepassing van de eenvoudige SVAT-area factor 12562/62500 verklaart het verschil.

## Omgeving
Nabijgelegen SVATs tonen uiteenlopend gedrag. Voor SVAT 198272 (149875, 496625), A=39623 m2, is qmodf 1549.537 m3 en QEXT4 256.335 m3 in februari D1. Voor SVAT 198273 (150125, 496625) komen beide wel ongeveer overeen. Vergelijkingen met aangrenzende cellen zijn aanwijzingen, geen bewijs van bronherkomst.

## Officiële documentatie en beperking
De NHI-site beschrijft qmodf als som van MODFLOW-stressen en qdr als aparte SIMGRO drainage-/infiltratieterm. De koppeling van MODFLOW-cellen aan SVATs loopt via `mod2svat.inp`. Dit is geen zekerheid dat de in WB18 berekende viercomponentensom de exacte originele qmodf-berekening is. Broncode van de LHM 4.3.3-koppelimplementatie is in deze sessie niet gevonden of uitgevoerd.

Bronnen:
- https://nhi.nu/modelcode/metaswap/metaswap-belangrijkste-modeluitvoer/
- https://nhi.nu/modelcode/metaswap/metaswap-gebruik/
- https://nhi.nu/modelcode/koppeling-modflow-metaswap/modflow-metaswap-praktijk/

## Gericht serverpakket
Het in deze sessie geleverde `LWKM_WB19_QMODF_Broncontrole.zip` bevat alleen **read-only** code. Met één CMD leest deze uitsluitend bronregels rond geselecteerde SVATs uit de oorspronkelijke `area_svat.inp` en `mod2svat.inp` en de oorspronkelijke QMODF-IDF van 2020-02-10. Hij registreert identiteiten, rasterwaarden en eenheden ter controle; onbekende regels worden niet automatisch als een bekend koppelcontract geïnterpreteerd. Dit is nog geen geverifieerde berekening van de oorspronkelijke LHM-koppelformule.

## Beslissingsvolgorde
1. Herleid de oorspronkelijke qmodf-waarde voor SVAT 198271 tot de waarde in het bron-IDF; controleer datum, sign, rasteruitlijning en eenheid.
2. Inspecteer `mod2svat.inp` voor oorspronkelijke SVAT/laag/celkoppeling. Bewijs de indexinterpretatie uit invoerspecificatie.
3. Vind de originele producer-/koppelcode en identificeer de exacte qmodf-berekening; pas daarna koppeling/ontbrekende term corrigeren.
4. Behoud 2020-WB18-bronwaarden en overzicht van nabijgelegen SVATs; geen historische productie aanpassen.
