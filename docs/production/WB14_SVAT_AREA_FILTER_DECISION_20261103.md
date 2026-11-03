# WB14: selectie op fysieke SVAT-ondersteuning en ontwatering (2026-11-03)

De projecteigenaar besluit dat cellen waarbij het opgetelde SVAT-oppervlak boven de volledige MODFLOW-celoppervlakte (62.500 m²) uitkomt, fysisch ongeldig zijn en niet in de gekwalificeerde ruimtelijke balans mogen worden meegeteld. Eerder WB13-resultaat: **7** van zulke cellen, terwijl de projecteigenaar **5** noemt. WB14 telt de originele bron opnieuw en rapporteert alle gevonden gevallen met coördinaten; het aantal wordt niet kunstmatig op 5 gezet.

Zeer kleine SVAT-oppervlakten kunnen administratieve placeholders zijn. Er is nog geen onderbouwde definitieve ondergrens. WB14 geeft daarom afzonderlijk alle fysisch geldige cellen en filters voor minimaal 0,01%, 1%, 10%, 50% en 99% SVAT-dekking. Het product rapporteert per geselecteerde populatie zowel de oorspronkelijke zeven-term-MetaSWAP-rest als de diagnostische aanvulling met de **volledige** MODFLOW-celflux DRN+RIV. De fluxen worden niet naar rato van de SVAT-oppervlakte aangepast. Voor alle varianten wordt voor en na exact dezelfde celpopulatie gebruikt.

SVAT 207543 blijft buiten de algemene balans vanwege de mogelijk afzonderlijke laag-1-beregeningsonttrekking. De onderliggende modeluitvoer wordt nergens overschreven. `qdr_recon=DRN+RIV` is een empirisch sterk ondersteunde ontbrekende balanspost, maar een oorspronkelijke softwarematige schrijfverplichting naar `qdr` is niet bewezen.

Uitvoering: het WB14-Python-ZIP-pakket van deze sessie, met `START_PROEF.cmd` en `START_2020.cmd`, leest oorspronkelijke `area_svat.inp`, de zeven decadische MetaSWAP-IDF's, MODFLOW-DRN/RIV-dagreeksen en het originele IBOUND. De tests voor selectie, gelijke ondersteuning en kalenderdecades zijn lokaal geslaagd; de werkelijke serverrun is nog niet uitgevoerd. Uitvoer: `decades.csv`, `year_2020.csv`, `invalid_areas.csv`, `population_coverage.csv`, `status.json`.

Gebruik de uitsluitingsresultaten niet om te beweren dat het volledige oorspronkelijke modelgebied sluit: bij iedere uitsluiting worden de daarmee verwijderde oppervlakte en fluxvolumes afzonderlijk gerapporteerd.
