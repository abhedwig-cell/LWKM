# LWKM W11 integratie-handoff: bestaande SVAT/HRU, DRA, BBC en aankomende MET (2026-10-20)

Actuele D1-aanvulling: de hieronder geplande consumerintegratie en synthetische pakketbouw zijn geïmplementeerd. De drie centrale productie-documenten, het D1-herstelpunt en docs/evidence/2026-10-20-work-d1 vormen het actuele uitvoeringsherstelpunt. Dit wijzigt geen van de onderstaande bron- en ontwerpbesluiten.

Status: interface-afspraak en geprioriteerd uitvoeringsplan, **geen** nieuw production admission.

## Actuele onafhankelijke evidence
- Work B PR #8: 427656 SVAT-memberships, 10242 HRUs, gereconstrueerde donor/representatieve SVAT en identieke SWP-contexten; raw-LHM en enrichment-bronbinding nog open.
- Work C2 PR #5: 10213 DRA-kandidaten, 29 zes-niveau-uitzonderingen; 101 SWAP 4.3.1-proeven over de gedekte 1971-periode geslaagd.
- Work A PR #9: FLF/FRF/FFF/GHB/WEL-route met expliciete oudere tekenautoriteit, dagelijkse fluxproductie op beperkte archiefbron; complete moderne serverreeksen nog niet gekoppeld.
- MetaSWAP Windows PR #10: werkelijke x64-executable met Windows-tests; daadwerkelijke serveruitvoer moet nog gecontroleerd binnenkomen.
- KNMI wind/duur: 50-stationscoördinaten op gebruiker-Windows bevestigd; 1970-2022 rasterproductie in uitvoering, nog geen finale raster-QA.

## Strikte interfaces
1. HRU population: precies 10242 IDs, unique SVAT-member mapping, originele SVAT-gewichten en versievaste member/source-ID. Nieuwe MET- en BBC-productie bindt deze snapshot en haar hash.
2. DRA: behoud 10213 afgewerkte kandidaten en 29 open uitzonderingen. Geen impliciete DRA-fallback. Drainage-eigenaarregels: DRARES > 100000 record weglaten, INFRES > 100000 geen infiltratie, H1 factor ontbreekt = geen infiltratie; natuur niet beregend.
3. BBC: per laag-1-cel/dag FLF+FRF+FFF+GHB+WEL (getekend positief toevoer); aggregeer naar HRU, lever mm/d. Dagwaarde = daggemiddelde puntwaarde in BBC; projecteigenaar accepteert SWAP-interpolatieverschil. Geen nieuw dagvolumebehoud-blokker. Bronperiode 1970-2022, geen stille extrapolatie.
4. MET: LHM ASCII brongrids leveren regen, ETref en overige variabelen. Aanvullend windgrid bevat windsnelheid 10m m/s, raw duration-grid een positieve dagfractie of NODATA. Valideer ALTW volgens SWAP 4.3.1 voor 10m. Bouw WET pas tijdens MET-consumptie, met **regen per SVAT**, niet eerst geaggregeerde HRU-regen:
    - regen=0 -> WET=0;
    - regen>0 en raw duur>0 -> raw duur;
    - regen>0 en geen geldige duur -> WET=0.1.
   Verwerp negatieve regen en ongeldige waarden; oorspronkelijke regenhoeveelheid blijft leidend. Bij ontbrekende LHM-meteorasterwaarde gebruikt SVAT op dezelfde dag de dichtstbijzijnde geldige rastercel, inclusief broncel/afstand in QA. Daarna oppervlaktegewogen naar HRU.
5. Output consumenten: HRU,date, dagelijkse MET-componenten inclusief wind_m_s en wet_fraction; HRU,date, BBC-componenten en nettoflux. Iedere bron/output krijgt logical ID, hash, periode, eenheid, geometrie, code/config-identiteit en status. Full MET/BBC pairs voor W11 uitsluitend bij complete brongebonden dekking.

## Werk voor lokale integratie zonder lopende serverrun te verstoren
- Controleer bestaande MET-consumer en de benodigde meteo-rasterbinders; voeg alleen ontbrekende WIND/WET_RAW-contracten en negatieve tests toe.
- Contracttests: wisselende positieve/0 regen per SVAT in dezelfde HRU, ontbrekende neerslagduur, regen nul ondanks positieve raw duur, nearest-valid meteorasterpixel, wind 10m/ALTW, datumgaten/duplicaten, SHA-wijziging, leap days, identieke incrementele rebuild.
- Maak server-naar-lokaal overdrachtsschema en automatische QA die de later binnenkomende meteo- en fluxproducten kan beoordelen zonder de bronreconstructie te herhalen.
- Kies een kleine reeks representatieve C2-HRU's voor een geïntegreerde moderne SWAP-smoke zodra volledig gekwalificeerde bronreeksen beschikbaar zijn.
- Werk documentatie en Leo-acceptatie bij op grond van werkelijke in plaats van verwachte resultaten.

## Opmerkingen
Dit document is nadrukkelijk geen bewijs dat de KNMI-grids, de volledige MET/BBC-catalogus of alle 10242 SWAP-runs al gemaakt zijn. De serverprocessen kunnen parallel doorgaan; geen dubbele zware uitvoering.
