# Technisch productiehandboek LWKM

Actueel op 20 oktober 2026, Work D1. Dit bestaande centrale document is bijgewerkt; de bestandsnaam blijft behouden. De keten levert kandidaten en kent zelf geen wetenschappelijke productie-admission toe.

## Bronautoriteit en integratie

De integratiebasis is `212d8c7e9396d62c45f3b26cddd6cefea1cc778d` op `work/lhm-hru-swap-workflow-v1`. PR's 3, 4, 5, 6, 7 en 9 waren daarin geïntegreerd. D1 neemt ook de exacte heads van Work B, PR 8 (`1a9e8eef340926ecc45bd7e7a8d3260e3344b6d8`), en MetaSWAP Windows, PR 10 (`4ab5eb139bd412652081e4b2bce64d9c7b9469f4`), als commitouders op. Die PR's worden hiermee niet afzonderlijk gesloten of als productie toegelaten.

Bestaande ontwerpbesluiten blijven authority:

| Onderwerp | Authority |
|---|---|
| Selectie, donors, representanten en context | [Work B](WORK_B_20261019.md), bronregister en interface-manifest |
| DRARES, INFRES, ontbrekende H1-factor, tulp | [C2-eigenaarbesluit](WORK_C2_OWNER_DECISIONS_2026-10-19.md) |
| Bestaande WEL/GHB | [Operationeel reconstructiebesluit](WORK_A_OWNER_RECONSTRUCTED_PRODUCTS_20261019.md) |
| FLF/FRF/FFF en tekens | [Bestaande vijfcomponenten-authority](WORK_A_FIVE_COMPONENT_AUTHORITY_20261019.md) |
| BBC-daggemiddelden | [BBC-timingbesluit](WORK_A_BBC_DAILY_MEAN_TIMING_DECISION_2026-10-20.md) |
| SVAT-oppervlak meteorologie | [Actuele area_svat-authority](W09_SVAT_AREA_AUTHORITY_DECISION_2026-10-20.md) |
| Vaste gewichten en ruimtelijke vervanging | [Gewichten](W09_PRECOMPUTED_HRU_METEO_GRID_WEIGHTS_2026-10-20.md), [nearest-valid](WORK_A_MET_NEAREST_VALID_GRID_DECISION_2026-10-20.md) |
| WIND, WET_RAW en WET | [Offline beleid](WORK_A_KNMI_WIND_WET_OFFLINE_POLICY_2026-10-20.md), [W11-interface](W11_INTEGRATION_HANDOFF_MET_BBC_2026-10-20.md) |
| Decadische ET en beregening | [ET-contract](ET_DECADE_HRU_REFERENCE_CONTRACT_2026-10-20.md), [Windows-product](../server/METASWAP_HRU_WINDOWS_2026-10-20.md) |

## Productketen

LHM-snapshots worden selectief geïdentificeerd en op de server verwerkt. Work B levert de onveranderlijke SVAT/HRU-populatie, donors, representanten en typed contexts. Work C2 levert de geselecteerde hydraulische drainageniveaus. De serverconsumers reduceren meteorologische rasters en bestaande dagelijkse laag-1-fluxen naar compacte HRU-dagproducten. D1 ontvangt die met hashes en bronmanifesten, schrijft MET/BBC en bouwt onveranderlijke SWAP-pakketten. De bestaande uitvoeringsrunner controleert de executable, de verplichte invoerbestanden, normale voltooiing, kalender en eindige dagelijkse uitvoer. Onafhankelijke waterbalanscontrole blijft nodig voor wetenschappelijke beoordeling.

De SWAP-kolom representeert MODFLOW-laag 1. Een HRU is een verzameling cellen en behoeft geen aaneengesloten vlak te zijn. De 427.656 oorspronkelijke geselecteerde SVATs en 10.242 HRU-identiteiten blijven behouden. Een donor vervangt parameters; hij verplaatst de oorspronkelijke meteorologische of grondwater-support niet.

## Oppervlakken en vaste meteorologische gewichten

`area_svat(3).inp` is voor W09 leidend, SHA-256 `352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc`. Membership `export_svat_HRU_NRU_10242(4).csv` heeft SHA-256 `13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319a667712f7f4`. De eerdere volledige bestanden uit de Windows-kwalificatie hebben dezelfde hashes; de verliesloze geselecteerde extractie in Git kan daarom voor deze velden opnieuw worden gebruikt.

De actuele meteorologische support bedraagt 25.514.516.032 m2. Work B bewaart daarnaast zijn historische 25.511.141.709 m2. Het verschil van 3.374.323 m2 is een expliciet geaccepteerd bronversieverschil voor W09, geen reden om de gekwalificeerde clustering opnieuw te berekenen. MODFLOW-volumeaggregatie blijft afzonderlijk gebaseerd op volledige 250 bij 250 m cellen. Deze oppervlakken zijn niet uitwisselbaar.

De vaste geometrie heeft 300 kolommen, 325 rijen, oorsprong (0, 300000) en cellen van 1000 m. `tools.met_grid_consumer.support` sommeert oorspronkelijke SVAT-oppervlakten per HRU en gridcel en deelt door het volledige HRU-SVAT-oppervlak. Het resultaat heeft 277.190 koppelingen. D1 reproduceert byte-identiek de gewichtentabel met SHA-256 `6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c`.

Dagelijks wordt de gecomprimeerde gewichtentabel gebruikt. Alleen leden van ontbrekende of semantisch ongeldige bronpixels vragen een extra zoekactie vanaf hun oorspronkelijke SVAT-coördinaat. Afstanden zijn in geprojecteerde meters; gelijke afstand wordt deterministisch opgelost met de laagste rij/kolom-index. Dit voorkomt een fout waarbij alle SVATs in één ontbrekende 1-km-cel dezelfde vervanger zouden krijgen, hoewel hun echte dichtstbijzijnde cel kan verschillen. De gewichten veranderen niet. De QA bewaart datum, variabele, SVAT, HRU, oorspronkelijke cel, vervangende cel, afstand en bronhash.

Verschillende rastergeometrieën worden in deze D1-consumer geweigerd. Zij vereisen vooraf een expliciete afzonderlijke supportbinding. NODATA-codes mogen per bestand verschillen. Een geheel ontbrekende noodzakelijke bronvariabele of dag wordt niet ruimtelijk of temporeel verzonnen.

## MET-consumer en eenheden

De canonieke interface bevat `hru_id,date,rad_kj_m2_d,tmin_c,tmax_c,vapour_pressure_kpa,wind_m_s,rain_mm_d,etref_mm_d,wet_fraction`. De raw rasterconsumer ontvangt dezelfde meteorologische variabelen, met `wet_raw_fraction` in plaats van de laatste kolom. WIND is al m/s op 10 m; geen voorcorrectie naar 2 m uitvoeren. De SWP heeft `ALTW=10.0`, in overeenstemming met het meethoogteveld van de SWAP-interface. SWAP verwerkt zelf zijn windhoogteparameter.

Regen en ruwe duur worden eerst op dezelfde oorspronkelijke ruimtelijke support gecombineerd:

* P=0: WET=0.
* P>0 en een geldige positieve duur: WET=duur.
* P>0 zonder geschikte positieve duur: WET=0.1 dagfractie, expliciet als schatting geaudit.

WET wordt daarna met de vaste HRU-gewichten gemiddeld. Middelen van neerslag vóór toepassing van deze regel is onjuist als droge en natte leden samen één HRU vormen. WET_RAW mag geheel zonder geschikte waarneming zijn; dan geldt bij positieve regen uitsluitend de vastgelegde 0.1-fallback. Een ontbrekend WET_RAW-bestand blijft een fout.

`tools.bind_met_rasters` selecteert per datum en variabele precies één bestaand bestand, hasht de bytes en maakt een uitvoerplan. Expliciet bevestigde bronunits kunnen met een vaste factor en offset automatisch naar canonieke units worden omgezet. Er is geen afleiding van units uit een bestandsnaam. De aangeleverde inventaris noemt de LHM-map FG als vapp; die naam alleen bewijst niet welke fysieke grootheid en schaal werkelijk in die bestanden staan. Ruwe LHM-eenheden en met name de dampdrukbinding moeten op echte bronmetadata worden gecontroleerd. Relatieve vochtigheid is geen SWAP-HUM in kPa.

## Dagelijkse grondwaterforcing en BBC

Gebruik ongewijzigd de bestaande reconstructies en tekenregels. Per laag-1-cel en dag:

`Q_ext = FLF + FRF + FFF + GHB + WEL`.

Positief betekent toevoer aan laag 1. De bestaande processor past alleen de reeds vastgelegde ruimtelijke bewerking toe, integreert bestaande intervalgemiddelden en sommeert over de HRU-celgroep. Intern lateraal transport valt daarbij algebraïsch weg; uitwisseling over de grens van de celverzameling blijft over. Omrekening: `q_mm_d=1000*Q_m3_d/A_m2`, met de volledige MODFLOW-celoppervlakte.

FLF, FRF, FFF, GHB en WEL blijven afzonderlijk beschikbaar, naast LAT en de som. RIV/DRN, berging en MetaSWAP-uitwisseling worden niet aan deze overige randvoorwaarde toegevoegd. PSGW is niet automatisch een WEL-onttrekking uit laag 1.

`tools.daily_budget_entry` bundelt de bestaande binder, processor en compacte export. Het heropent geen reconstructie. Een dagcheckpoint controleert code, configuratie, betrokken bronhashes en beide uitvoerhashes. Alleen gewijzigde dagen worden opnieuw numeriek verwerkt. De intervalselectie is vooraf per dag geïndexeerd, zodat een lange reeks niet voor iedere dag alle historische intervallen opnieuw doorzoekt.

`tools.daily_forcing.effective_bbc` schrijft gewone dagelijkse knopen, met mm/d gedeeld door 10 naar cm/d. SWAP mag tussen die knopen interpoleren. Er is geen trapfunctie of volumecorrectie in de productieroute en er wordt geen extra dag buiten de bronperiode toegevoegd. De historische duplicate-midnight-proef blijft uitsluitend met expliciete experimentele opt-in bereikbaar. Haar afwijkingen zijn geen heropende productiestopper. De 36.600-rijengrens wordt op de werkelijke BBC-tabel gecontroleerd.

## DRA, gewassen en pakketten

C2 blijft 10.213 geldige DRA-kandidaten en 29 beschermde uitzonderingen leveren. DRARES boven 100.000 dagen leidt tot weglaten van de betrokken fysieke bijdrage; INFRES boven 100.000 en ontbrekende H1-factor leiden tot geen infiltratie. Er worden geen weerstanden afgekapt of niveaus ongemerkt heringedeeld.

De opgeslagen DRA-bytes bestrijken de oude proefjaren. `tools.dra_period` kan dezelfde reeds gekozen checkpointniveaus voor een andere runperiode serialiseren. Zomer- en winterpeilen blijven dezelfde parameters. Expliciete maandreeksen worden alleen herhaald als zij precies één gesloten, volledig maandelijk jaarpatroon vertegenwoordigen; een andere reeks wordt geweigerd. Dit is hergebruik van de bestaande parametrisering, geen bewijs dat peilbeheer werkelijk ieder historisch jaar gelijk was.

`tools.prepare_d1_assets` koppelt de bestaande workbooktabellen Irrigatie en Meteo aan originele gewastemplates. De representatieve SVAT bepaalt de bestaande landgebruiksvlag. Natuur krijgt altijd SCHEDULE=0, naast SWIRFIX=0; historische MetaSWAP-beregening bij natuur verandert die productieregel niet. De catalogus bewaart bronhashes en eventuele aanpassing. Tulp gebruikt de expliciet vastgelegde PM-route. Alleen de eerder gekwalificeerde constante gras-CF wordt overgenomen. Appelbomen zonder gekwalificeerde CF blijven geblokkeerd, HRU's 4243 tot en met 4246.

`tools.work_d1` ontvangt gehashte dagproducten, indexeert alleen gewijzigde shards in SQLite, genereert HRU-specifieke MET/BBC en combineert die met bestaande contexts, DRA en brongebonden CRP/CO2. Nationale rasters gaan niet mee naar de lokale ontvangst. Per fase blijft het geheugen begrensd tot een dag of één HRU-reeks. Alle uitvoerbestanden worden aan inhoud en bronbinding gekoppeld. Een compleet pakket heeft expliciete verwijzingen, volledige periode, geverifieerde hashes en geslaagde preflight. De builder kan geen productie-admission verlenen.

## MetaSWAP-acceptatie

De bestaande producer schrijft per geconfigureerd decade-einde een HRU-CSV, QC-CSV en SHA-marker, met originele variabelen MSW_EBS, MSW_EIC, MSW_EPD, MSW_ESP, MSW_TACT, MSW_TPOT, PSSW, PSGW en BDGETACT. De eenheid is volgens het vastgelegde projectcontract m3/m2 per decade, na factor 1000 mm/decade. Tekens blijven behouden.

De zelfstandige C++-acceptor leest de feitelijke `sources.csv`, controleert aaneengesloten kalenderdecades en de negen variabelen, alle HRU's en de juiste lengte van de laatste decade. Hij controleert oorspronkelijke area/membership/executable-hashes, rekent de HRU-support onafhankelijk uit die invoer opnieuw na, controleert rasterbronhashes en uitvoer/QC-hashes, eindigheid, dekking, volledigheidsvlag en alle afgeleide sommen. Ontbrekende waarden blijven ontbrekend; TPOT zit niet in actuele ET.

De compacte export bevat jaarlijkse HRU-sommen met volledigheidsaantallen, seizoenssommen op populatieniveau, decadische populatiegemiddelden, aparte dekking/residual-QA, support en bronhashes. DJF is hier een kalenderjaarselectie van januari, februari en december, geen winter die naar het volgende jaar wordt verschoven. Een gedeeltelijk geconfigureerd jaar wordt als zodanig aangeduid. Een diagnosegrens van 0.0001 mm voor het ET-residu is geen wetenschappelijk acceptatiecriterium.

Standaard worden de echte rasterbronnen opnieuw gehasht. De expliciete optie `--recorded-sources-only` kan reeds vastgelegde bronhashes inspecteren zonder de rasters; de uitvoer meldt dan dat herhashing niet is gedaan. `COMPLETE.txt` bevestigt alleen een volledig afgewerkte compacte export. Exit 2 betekent dat ontbrekende HRU-waarden zijn aangetroffen. Geen van beide statussen bewijst correcte bronsemantiek of productie-admission. `tools.accept_compact_metaswap` controleert lokaal de compacte overdracht.

## Tests, uitvoering en grenzen

Voer lokaal `python -m pytest -q` uit. De testverzameling bevat numerieke MET/SVAT-regressie, oorspronkelijke coördinaten bij ontbrekende pixels, nulwaarden, ties, leap days, WET, importhashes, vijfcomponentensom, corruptie, herstart, natuur, DRA-uitzonderingen, native C++-acceptatie en echte brongebonden pakketpreflight met synthetische forcing.

De landelijke integratie wordt reproduceerbaar gestart met `python -m tools.qualify_work_d1 --workbook ... --templates ... --output ...`. Zij gebruikt echte support, contexts en C2-data, maar uitsluitend synthetische meteorologie en fluxen. Het definitieve bewijs staat in `../evidence/2026-10-20-work-d1/`.

De serverlevering bevat zelfstandige Windows-consumers. De MET- en budgetexecutables bundelen hun runtime; een geïnstalleerde Python of ontwikkelomgeving is niet nodig. Native Windows-kwalificatie wordt apart in GitHub Actions vastgelegd. De bestaande 101 C2-berekeningen worden behouden en niet als nieuw D1-modelresultaat opgevoerd. De in Tools(2).zip teruggevonden executable is versie 4.2.261 en vervangt de gepinde SWAP 4.3.1 niet.

Overige wetenschappelijke gates, waaronder ruwe LHM/enrichment-lineage, ruimtelijke representativiteit, meteorologische bronunits, echte serverdekking en ANIMO-uitvoercontracten, blijven zichtbaar in het actuele [blockerregister](../evidence/2026-10-20-work-d1/blockers.json). Operationele stappen en concrete commando's staan in het [runbook](RUNBOOK_20261019.md).
