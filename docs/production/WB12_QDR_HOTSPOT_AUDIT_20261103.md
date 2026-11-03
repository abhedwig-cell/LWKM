# WB12: qdr-hypothese en hercontrole hardnekkige ruimtelijke afwijkingen (2026-11-03)

## Documentatiecontrole
De MetaSWAP Input/Output Reference Manual V8.1.2.4 beschrijft qdr als SIMGRO-drainage/infiltratie, qmodf als MODFLOW-stressen en qdrmod als een afzonderlijke drainagecorrectie. De verzadigde balans kent qsat = qmodf + qdr + qspgw. De definitie bewijst **niet** dat de oorspronkelijke LHM 4.3.3-rekencode de in MODFLOW berekende DRN- en RIV-fluxen naar qdr had moeten doorzetten. Ook een nulwaarde in qdr mag niet zonder codecontrole als modelbug worden geclassificeerd.

## WB11-resultaten, 2020
Gebruiker leverde alle 36 decade-top100-bestanden en nationale resultaatsommen aan. De niet-gecorrigeerde 7-term MetaSWAP-rest is +8,094 miljard m3. Na diagnostische toevoeging van originele MODFLOW DRN+RIV (samen -8,220 miljard m3) resteert netto -0,125 miljard m3. De som absolute celresten daalt van 10,172 naar 0,381 miljard m3. Dit is sterke empirische steun voor een ontbrekende ontwateringsterm **in onze 7-term-balans**, geen bewijs voor een fout in de originele uitvoer.

De 3.600 records uit de 36 decade-top100-lijsten vertegenwoordigen 163 onderscheiden opgeslagen celindices; 67 daarvan komen in elke decade voor. Voor een deel zijn de RIV-fluxen groot terwijl de zeven MetaSWAP-termen nagenoeg nul zijn.

## Nieuwe bevinding: indexeringsfout in WB11-top100
WB11 verwijdert SVAT 207543 bij het selecteren van de 'eligible' cellen, maar gebruikt daarna bij het terugzoeken van de honderd grootste afwijkingen de niet-gefilterde indexlijst. Daardoor kunnen gerapporteerde coordinaten na de positie van de uitzondering één positie verschoven zijn. Dit beïnvloedt niet de landelijke volumes en MAE, **wel de top-100-locaties**. Een nieuwe WB12-serverdiagnose corrigeert de index, koppelt de ruimtelijke SVAT-oppervlaktefracties en onderzoekt persistente hotspots. Eerdere coordinaten zijn daardoor voorlopig niet geverifieerd.

## Te leveren WB12-bevindingen
- Top100-cellen per decade met gecorrigeerde rasterindex en ondersteuning.
- Persistente hotspots, frequentie, teken en RIV/DRN dominantie.
- SVAT-oppervlak versus MODFLOW-volledig celoppervlak.
- Oorspronkelijke relevante regels uit SEL_KEY_SVAT_PER.INP/PARA_SIM.INP, als aanwezig.
- Geen wijziging in brondata, fluxen of qdr.
- De LHM 4.3.3-koppelcode blijft nog te inspecteren; configuratie en uitvoerselectie zijn niet gelijk aan de interne berekening.
