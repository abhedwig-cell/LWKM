# LWKM W09: vaste HRU-gewichten per meteorastercel (eigenaarbesluit 2026-10-20)

Eenmalig afleiden uit originele SVAT→HRU-membership, SVAT-oppervlakten en de geometrie van elk meteoraster:

weight(h,g) = sum(area_svat voor SVATs van HRU h in rastercel g) / sum(area_svat voor alle SVATs van HRU h).

Maak een gehashte tabel met HRU_ID, METEO_GRID_ID (of row/col), AREA_M2, WEIGHT en rastergeometrie-ID, plus bronidentiteiten/versie. Weiger ontbrekende of dubbele SVAT-bindingen, ongeldige oppervlakten, raster-overlap en gewichtensommen die niet op 1 uitkomen. Herbouw de tabel alleen als membership, oppervlakten of rastergeometrie wijzigen.

Dagelijkse meteorologische waarde = som_g weight(h,g) * M(g,date). Dit voorkomt dagelijkse herhaling van alle 427656 SVAT-joins.

Voor ontbrekende rasterwaarde: vervang per datum en variabele door de dichtstbijzijnde geografisch geldige rastercel, behoud de originele gewichten en audit bron- en vervangingscellen/afstand. Geldige nul blijft nul. Rastervariabelen met verschillende geometrie krijgen eigen gewichtentabel; gelijke geometrie kan een tabel delen.

Belangrijke WET-regel: WET hangt af van neerslag op dezelfde oorspronkelijke SVAT/gridlocatie. Combineer eerst de LHM-neerslag en raw KNMI-neerslagduur op dezelfde ruimtelijke support met WET=0 als P=0, WET=raw bij P>0 en raw>0, en WET=0.1 bij P>0 zonder positieve raw. Aggregeer daarna met dezelfde vaste HRU-gridgewichten. Bij verschillende neerslag- en raw-duurrasters of SVAT-specifieke bronbindingen kan eerst een grid-to-SVAT-resampling nodig blijven: vermijd voorafgaande gewichtscompressie die deze ruimtelijke logica verandert.

Dit is een uitvoeringscontract, geen bewijs van gekwalificeerde productie. Test eenmalige gewichten, jaarlijkse herbruikbaarheid, datumafhankelijke nearest-valid, WET-consistentie en vergelijk numeriek tegen onafhankelijke originele SVAT-gewogen aggregatie.
