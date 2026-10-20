# LWKM ontwerpbesluit: decadische ET- en beregeningsreferentie voor HRU's
Datum: 2026-10-20
Status: projecteigenaarbesluit over datacontract; broninventarisatie, uitvoering en wetenschappelijke kwalificatie volgen.

## Doel en afbakening
Voor elk van de 10.242 HRU's wordt een oppervlaktegewogen referentietijdreeks uit de decadische MetaSWAP/LHM-uitvoer samengesteld. Doel is later de SWAP-HRU-respons op totale actuele verdamping beter te laten aansluiten op de gemiddelde LHM-celgroep. Dit besluit vraagt nog **geen** grootschalige CRP-kalibratie of responsbibliotheek.

Een decade betreft kalenderdagen 1-10, 11-20, en 21-laatste dag van de maand (inclusief variabele lengte). Bronbestanden zijn beschikbaar op de NHI/LHM-server en moeten daar met bestaande SVAT→HRU-membership worden verwerkt, bij voorkeur tot een compacte, gehashte HRU-decadetabel; vermijd blind overhalen van nationale IDF-rasters.

## Oorspronkelijke MetaSWAP-variabelen, ongewijzigd bewaren
- MSW_EBS: kale-bodemverdamping
- MSW_EIC: interceptieverdamping
- MSW_EPD: plas-/pondingverdamping
- MSW_ESP: verdampingsverlies bij beregening
- MSW_TACT: actuele transpiratie
- MSW_TPOT: potentiële transpiratie
- PSSW: beregeningsgift met herkomst oppervlaktewater
- PSGW: beregeningsgift met herkomst grondwater
- BDGETACT: aparte bestaande totale-actuele-ET-controlebron; verifieer de precieze bronfamilie, eenheid, tekenconventie en relatie tot vijf ET-componenten.

## Afgeleide indicatoren voor vergelijking met SWAP
- E_soil_compare = MSW_EBS + MSW_EPD
- E_interception_compare = MSW_EIC + MSW_ESP
- T_actual = MSW_TACT
- ET_actual_components = MSW_EBS + MSW_EPD + MSW_EIC + MSW_ESP + MSW_TACT
- Irrigation_total = PSSW + PSGW
- T_reduction = MSW_TPOT - MSW_TACT
- Stress_fraction = 1 - MSW_TACT / MSW_TPOT, uitsluitend waar TPOT > 0 en de betekenis van de bronwaarden dit toestaat.
- ET_balance_residual = BDGETACT - ET_actual_components, ná consistent maken van periodelengte, eenheid en tekenconventie.

De onderverdeling in E_soil_compare en E_interception_compare is een **vergelijkingsconventie**, geen fysische gelijkstelling van bodem/plasverdamping of interceptie/beregeningsverlies. Behoud de vijf oorspronkelijke ET-componenten om afzonderlijke verschillen te analyseren.

## Aggregatie
- Controleer of elk bron-IDF de decadehoeveelheid of een gemiddelde flux per dag representeert; converteer expliciet naar mm per decade volgens het werkelijke aantal dagen in de periode.
- Koppel oorspronkelijke SVAT-cellen aan de bestaande HRU-populatie en gebruik de gekwalificeerde oppervlaktesupport/gewichten. Bepaal geen geografische HRU-buitenrand; HRU's hoeven niet aaneengesloten te zijn.
- Valideer geometrie, NODATA, dekking, duplicaten, IDs en de som van oppervlaktes.
- Geen impliciete nulvulling, herschaling van resterende celgewichten of tijdsextrapolatie. Noteer incomplete HRU-decades als onvolledig.
- Som/vergelijk eerst op oorspronkelijke SVAT- en decadelaag waar mogelijk en daarna op HRU-niveau; sla beide controleresiduen op.
- Registreer alle originele bronbestanden, hashes, producent-/code-identiteit en invoer/uitvoerprovenance.

## Wetenschappelijke prioriteit
De totale actuele ET heeft het hoogste gewicht in de latere beoordeling. Verschillen in TACT, EBS+EPD en EIC+ESP moeten worden gerapporteerd maar krijgen vooralsnog geen zwaar kalibratiegewicht: MetaSWAP en SWAP beschrijven de processen verschillend. BDGETACT wordt een primaire totale-ET-referentiekandidaat zodra de controle van de bronsemantiek en componentsom geslaagd is. Bij verschil niet stilzwijgend BDGETACT of de componentsom als exact kiezen.

Voor SWAP/ANIMO worden zeven beheerprofielen onderscheiden: gras, mais en bouwland ieder met/zonder beregening, en natuur alleen zonder beregening. **Natuur wordt in de moderne HRU-runs nooit beregend.** Historische PSSW/PSGW bij natuur worden als diagnostische uitzondering bewaard in plaats van stilzwijgend de productieregel te veranderen. PSSW en PSGW zijn beregeningsgiften; PSGW is niet automatisch een MODFLOW-laag-1 WEL-onttrekking.

## Vervolg
1. Vind de oorspronkelijke decadische IDF-bronfamilies op de server en bevestig hun eenheden/definities en kalenderdekking.
2. Implementeer een server-side streaming SVAT→HRU-aggreger, tests en per-file SHA-256 plus compacte Parquet/CSV-output.
3. Maak een dekkingsoverzicht en residualen BDGETACT minus componentensom.
4. Analyseer ET en irrigatie per jaar, decade, BOFEK, landgebruik, beregeningsregime en hydrologische omstandigheden.
5. Ontwerp pas na deze referentieanalyse een beperkte SWAP-responsbibliotheek en parametrische HRU-afstemming; houd droge en natte jaren apart en test op niet-gebruikte jaren.

Geen productie-admission uitsluitend op basis van dit ontwerpdocument.
