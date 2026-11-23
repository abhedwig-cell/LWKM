"""De 49 kolommen van Frank, ongewijzigd overgenomen uit v06."""
HEADERS = ['SVAT/ HRU', 'N aantal SVAT’s', 'Opp_svat/ hru', 'Landuse LHM (22)', 'Landuse ANIMO (4 tekst)', 'LU4', 'LU2', 'Bodem370', 'Bodem79', 'Pawn21', 'Grondsoort4', 'Grondsoort 2', 'Gtnr', 'GLG m-mv', 'GHG m-mv', 'GG ((GHG+GLG)/2)', 'Dynamiek (GLG-GHG)', '5% percentiel grondwaterstand op decadebasis voor reeks 30 jaar', '95% percentiel grondwaterstand op decadebasis voor reeks 30 jaar', 'Kwelklasse4', 'Neerslag (mm/j)', 'Beregening', 'Evapotranspiratie', 'Verdamping gewas', 'verdamping interceptie', 'Verdamping bodem', 'Oppervlakkige afstroming', 'Ontwatering', 'Fldrou1', 'Fldrou2', 'Fldrou3', 'Fldrou4', 'Fldrou5', 'Infiltratie', 'Fldrin1', 'Fldrin2', 'Fldrin345', 'Netto kwel/wegzijging (wegzijging (neg) + kwel (pos))', 'Laterale stroming (netto)', 'Onttrekkingen (uit laag 1)', 'General head boundary', 'Wegzijging', 'Kwel', 'QModF', 'Bergingsverandering (MetaSWAP)', 'Waterbalansfout MetaSWAP', 'Waterbalansfout overall', 'Indicator gecorrigeerde (Flevoland) of vervangen (herschikking) Svats', 'Gebiednummer']

ID, COUNT, AREA, FLAG, REGION = (HEADERS[i] for i in (0, 1, 2, 47, 48))
NUMERIC_COLUMNS = HEADERS[13:19] + HEADERS[20:47]
CATEGORICAL_COLUMNS = HEADERS[3:13] + [HEADERS[19]]
NET = HEADERS[37]
P5, P95 = HEADERS[17:19]

MF_COLUMNS = HEADERS[27:43]
AUDIT_FIELDS = ["FLF_KWEL_m3", "FLF_WEGZIJGING_m3", "RIV_SYS1_INFILTRATIE_m3", "RIV_SYS1_ONTWATERING_m3"]
CELL_AREA = 62500.0
