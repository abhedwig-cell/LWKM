# ET-CAL01 herstelpunt

Lees `docs/production/ET_CAL01_METHOD_2026-10-20.md` en de evidence onder `docs/evidence/2026-10-20-et-cal01/`.

De methode is geïmplementeerd: bestaande pakketoverlays, bestaande SWAP-runner, dagelijkse extractie naar kalenderdecades, native MetaSWAP-HRU-adapter, geregulariseerde ET-comparator, centrale gevoeligheden met singular-value-diagnostiek, begrensd kwadratisch responsoppervlak en HRU-profielselectie met onafhankelijke jaren en expliciete blokkades.

Er zijn 32 geslaagde echte SWAP 4.3.1-onderzoekruns: drie C2-pakketten maal negen parameterpunten en één tussenpunt, plus twee kunstmatige hydrologische foutproeven. De drie uitgangsruns reproduceren C2 exact. Daarnaast zijn vijf volledig synthetische meerjaarsscenario's geslaagd. Alle 439 repositorytests en drie subtests slagen.

Er is geen echte MetaSWAP-HRU-referentie ontvangen en geen HRU feitelijk gekalibreerd. De 1971-pakketten eindigen op 20 december en leveren geen onafhankelijke jaarvalidatie. Mais, natuur en beregende landbouw zijn nog niet als echte responscases gekwalificeerd. De bestaande landelijke uitgangsparameters blijven operationeel behouden.

De volgende inhoudelijke stap is de echte native HRU-decades controleren zodra de al geproduceerde serverresultaten beschikbaar zijn. De D1-compacte jaar/populatietabellen bevatten onvoldoende informatie voor HRU-specifieke decadefits. Gebruik de native YYYYMMDD.csv plus hashmarkers, zonder nationale rasters over te halen. Eerst units/tekens en BDGETACT-residuen beoordelen, dan brongebonden meerjaarspakketten met correcte giften en hydrologie selecteren. Geen aanvullende upload of serverhandeling is voor het herhalen van deze lokale kwalificatie nodig.

Feddes is bij gras 7876 ongevoelig en bij bouwland 7870 zwak identificeerbaar. Laat die schaalfactor daar op één totdat onafhankelijke droge referentiejaren de tweede richting ondersteunen. Pas de gevoeligheidsrangorde van deze drie cases niet landelijk toe. Automatische irrigatie wordt door de adapter geweigerd; de vaste giftenroute moet eerst via de bestaande pakketketen worden gebonden.
