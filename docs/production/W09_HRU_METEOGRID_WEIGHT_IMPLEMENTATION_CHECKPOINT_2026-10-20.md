# W09 implementatiecheckpoint 20 oktober 2026

Actuele D1-aanvulling: de vaste-gewichtencode staat inmiddels in Git en is geïntegreerd met tools.met_grid_consumer. De volledige 427.656-SVAT-tabel reproduceert de bestaande 277.190 koppelingen byte-identiek. Echte meteorologische productie-admission volgt niet uit deze test; zie het centrale technische handboek en D1-evidence.

Er is lokaal een zelfstandige Python-prototypeimplementatie gebouwd voor vaste HRU-meteogridgewichten (`hru_grid_weights.py`, levering `lwkm_grid_weights_v1.zip`). De testmodule slaagt in 3/3 synthetische gevallen (directe SVAT-weging, nearest-valid zonder herweging, ongeldige geometrie). De code is als overdrachtspakket beschikbaar; het bronbestand is nog niet in deze repository ingecheckt en moet voorafgaand aan geïntegreerde productie op de passende modulelocatie worden opgenomen en opnieuw getest.

Rekenregel: per HRU en meteogridcel eerst som van SVAT-oppervlakten, delen door volledig HRU-SVAT-oppervlak. Gewichten blijven constant zolang membership, SVAT-gebieden en rastergeometrie ongewijzigd zijn. Dagelijkse ontbrekende meteocelwaarde via de dichtstbijzijnde geldige cel invullen vóór toepassing van de vaste gewichten; geen dynamische hernormalisatie.

Voor WET eerst LHM-neerslag en ruwe neerslagduur op dezelfde SVAT-ruimtelijke support combineren: neerslag=0 => WET=0; neerslag>0 met geldige positieve duur => die duur; anders WET=0,1. Dan pas oppervlaktegewogen HRU-gemiddelde. Niet blind vooraf gridgewichten samenpersen indien neerslag en duur verschillende rastergeometrieën of SVAT-toewijzingen hebben.

Open: exacte huidige SVAT-coördinaten/UOPP-autoriteit verbinden; echte 10.242-HRU-test; geïntegreerde dagbatch en full-period run; numerieke regressie met oorspronkelijke SVAT-route; gehashte inputbinding. Geen production admission.
