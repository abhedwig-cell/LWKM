# Overdracht aan Leo: actuele acceptatie en herhaalbaarheid

Bijgewerkt voor Work D1 op 20 oktober 2026. Dit is een overdrachtspakket; er is geen bericht aan Leo verstuurd. De bestaande bestandsnaam blijft behouden. Ontwerpbesluiten staan in de eerdere authoritydocumenten, niet opnieuw in deze checklist.

De ingang is [het D1-herstelpunt](../handoff/LWKM_WORK_D1_HANDOFF_2026-10-20.md), gevolgd door het [technische handboek](ARCHITECTURE_20261019.md), de [operationele handleiding](RUNBOOK_20261019.md) en het [leesbare hoofdrapport](REPORT_20261019.md). Gebruik daarnaast `config/production/work-d1-contract-v1.json` en de exacte commit bij `docs/evidence/2026-10-20-work-d1`.

| Onderdeel | Te controleren | Betekenis van slagen |
|---|---|---|
| Integratie | Shared head, Work B #8 en MetaSWAP #10 zijn voorouders van D1; PR 3-10-status is geregistreerd | Bestaande code en evidence blijven integraal behouden |
| Populatie | 427.656 unieke oorspronkelijke SVATs, 10.242 HRU-contexten, bestaande donors/representanten | Gekwalificeerde snapshotreproductie, geen nieuwe raw-LHM-admission |
| Oppervlakte | Actuele W09-support en gewichtentabelhash gelijk aan eigenaarbesluit | Geen dagelijkse herweging en geen donorverplaatsing van forcing |
| MET | WIND op 10 m, ALTW=10, WET vóór HRU-middeling, geaudite nearest-valid, geen datumgaten | Software en complete brongebonden meteorologische interface |
| Grondwater | FLF/FRF/FFF/GHB/WEL afzonderlijk, som en volledige-celoppervlakte correct | Broncomponenten en geaccepteerde daggemiddelde BBC-route blijven herkenbaar |
| DRA | 10.213 kandidaten, 29 expliciete uitzonderingen, dezelfde geselecteerde checkpointniveaus | Geen nieuwe compressie of stil weglaten van moeilijke HRU's |
| Beheer/gewas | Natuur zonder vaste en automatische beregening; tulp PM; gras alleen gekwalificeerde constante CF | Geen stilzwijgende wijziging van ET-route of beheer |
| Appelbomen | HRU 4243-4246 afzonderlijk geblokkeerd | Geen verzonnen gewasfactor of onbevestigde PM-keuze |
| MetaSWAP-acceptor | Native Windows-executable, werkelijke sources.csv, oorspronkelijke input-, raster- en outputhashes, alle HRU's en dekking | Technische acceptatie van echte bestanden; wetenschappelijke beoordeling blijft apart |
| Compacte ET-export | Jaarlijkse HRU-sommen, seizoenen, decades, residualen, ontbrekende waarden en bronhashes | Analyse zonder het volledige grote archief over te halen |
| Import/herstart | Ongewijzigde shards hergebruikt; wijziging, corruptie, duplicaat en gat worden afgehandeld | Herhaalbare gecontroleerde gegevensontvangst |
| Runpakketten | Verplichte brongebonden assets, periode, preflight en manifest correct | Compleet onderzoekspakket, geen automatische productie-admission |
| Echte berekening | Exacte 4.3.1-engine, normale voltooiing, volledige dagelijkse uitvoer, waterbalans | Technisch en fysisch getoetste run binnen de gelezen bronperiode |
| ANIMO | Expliciete uitvoerselectie, laagmapping, units en uitgevoerde overdrachtstoets | Afzonderlijke ANIMO-acceptatie, niet afgeleid uit SWAP-voltooiing |

D1 bouwt in de landelijke integratie 10.209 pakketten met synthetische forcing. De exacte definitieve hergebruikcijfers en tests staan in de evidence. De eerder uitgevoerde 101 C2-modelberekeningen blijven behouden. Ongewijzigde proeven worden niet herhaald om een hoger uitvoeringsaantal te tonen.

De echte nieuwe serverresultaten, de feitelijke KNMI-rasterproductie en volledige grondwaterreeks zijn nog niet door D1 gelezen. Het ontbreken van originele WEL/GHB-budgetten en exacte dagvolumebewaring door BBC-interpolatie zijn geen open productiestoppers meer. Wel open zijn de concrete datatoegang, bevestigde meteorologische bronunits, de geregistreerde wetenschappelijke HRU/enrichment-gates en de fysieke kwalificatie van echte runs. Zie het [actuele blockerregister](../evidence/2026-10-20-work-d1/blockers.json).

Bij overdracht hoort de Windowslevering met SHA256SUMS, de gehashte workflowconfiguratie, de compacte bronmanifesten en de exacte Git-versie. Leo hoeft nationale rasterarchieven niet over te nemen om de lokale ontvangst en pakketbouw te herhalen. Voor herhaling van serveraggregatie blijven die rasters op de server zelf nodig.
