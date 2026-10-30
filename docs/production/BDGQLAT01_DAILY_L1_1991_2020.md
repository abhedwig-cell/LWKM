# BDGQLAT01: dagelijkse netto laterale laag-1-celflux, 1991–2020

Status: ontwerpcontract. Deze commit implementeert **nog geen producer**, en kwalificeert geen nieuwe IDF-uitvoer.

## Doel en afbakening
Maak voor iedere kalenderdag van 1991-01-01 tot en met 2020-12-31 (10.958 dagen) één nieuw IDF met de netto laterale volumeflux naar **MODFLOW-laag 1**, per MODFLOW-cel. Uitgangspunt zijn de **bestaande gereconstrueerde dagelijkse FRF- en FFF-IDF's**. Nooit originele reconstructies overschrijven. Geen hernieuwde MODFLOW-budgetreconstructie.

## Gezaghebbende bron
Herbruik exact de face-semantiek, geometrie, IBOUND-validatie en current-minus-previous-operaties van BBC09 (PR #24, branch `work/bbc09-net-faces-20261029`). BBC08 CELL_NET is onjuist voor de geïdentificeerde saved-face-bestanden en mag niet als uitgangspunt dienen. BBC09 laat zien dat FRF/FFF saved incoming face components zijn; controleer de daadwerkelijke producerfunctie en indexconventie voordat deze berekening wordt aangesloten.

Definieer per cel:
- `LAT_FRF = FRF_current - FRF_previous_column`
- `LAT_FFF = FFF_current - FFF_previous_row`
- `BDGQLAT = LAT_FRF + LAT_FFF`

Beide componenten zijn **netto toevoer aan laag 1** bij positieve waarde. De algebra hierboven is de **BBC09-conventie**, geen vrijbrief om generiek naar MODFLOW FLOW-RIGHT-FACE/FLOW-FRONT-FACE van een andere oorsprong te kijken. Omwisseling van indexrichting of raw-native face-waarden vereist herkwalificatie.

## Maskering en grenzen
Gebruik het originele, met SHA256 gebonden IBOUND-masker. Alleen echte buitengrenzen of expliciet inactieve voorgangercellen mogen een ontbrekende predecessor als nul behandelen. Ontbrekende data bij actieve cellen moet de dag laten falen. Niet-nul waarden op gesloten forward faces zijn fout. Cellen zonder gekoppelde SVAT blijven in de volledige laag-1-rasterbalans aanwezig. NODATA buiten het relevante actieve domein, geen impliciete nul.

## I/O-vereisten
- Invoer: bestaande, herleidbare FRF/FFF-IDF's, oorspronkelijke IBOUND, bevestigde formaat- en eenhedencontracten; expliciete paden via manifest.
- Uitvoer: één `BDGQLAT_YYYYMMDD.IDF` per dag in **nieuwe** outputdirectory, eigen provenance-manifest, dagstatus/checkpoints, dagtotalen en foutlog. Gebruik hetzelfde raster, coördinatenstelsel, nodata-definitie en nauwkeurigheid als de door BBC09 gekwalificeerde reader/writer.
- Eenheid: laat de gekwalificeerde bronsemantiek leidend zijn; schrijf geen mm/d als de berekening celvolume/tijd oplevert. Leg `m3/day` alleen vast als dit werkelijk door de producer is bevestigd. Conversie naar mm/d pas na bewezen oppervlaktekoppeling.
- Windows-serverprocedure via CMD, zonder verplichte Python-installatie op NHI-server. Hergebruik waar mogelijk de bestaande native IDF-reader/writer en Windows-bouwketen. Eén dag per checkpoint; herstart overslaat uitsluitend volledig geverifieerde dagen.

## Test- en acceptatiecontract
1. Test met analytisch tweecellen- en 2D-raster: interne face heft exact op.
2. Onafhankelijke vergelijking van sum(cel BDGQLAT) met buitengrenssaldo, met expliciete mask- en noodata-afhandeling.
3. Vergelijk uitkomsten op de zes bestaande reële BBC09-research-HRU snapshots; overeenstemming van HRU-sommen en onafhankelijke directe HRU-boundary-berekening, met identieke area authority.
4. Bronhashes inclusief eerder gerapporteerde afwijking van **volledige FRF-file SHA256** zichtbaar houden; inhoudelijke overeenkomst alleen geldt niet als hash-identiteit.
5. Controleer volledige kalenderdekking: 10.958 dagen, geen duplicaten, missende dagen of stilzwijgende nulwaarden.
6. Manifest omvat bronpaden, bronhashes, BBC09-commit, IBOUND-hash, softwareversie, uitvoerhashes, eenheid, datum en sign-conventie.
7. Dagtotalen en globale 1991–2020 volumes; massaconservering van interne laterale fluxen.

## Gebruik in latere balansen
BDGQLAT is een **laterale laag-1-celbudgetterm**. Niet opnieuw FRF en FFF naast BDGQLAT bij dezelfde laag-1-balans optellen. Voor aggregatie binnen HRU's vallen interne faces tegen elkaar weg; een directe HRU-grensvergelijking is onafhankelijke QA. FLF is de verticale laag-1/laag-2-grensflux. Koppelflux MetaSWAP/MODFLOW is intern voor de gezamenlijke balans; MODFLOW-berging is vooralsnog niet beschikbaar en mag niet op nul worden gezet.

## Nog uit te voeren
Codeproducer aansluitend op BBC09 implementeren, native Windows-EXE bouwen, serverpaden verifiëren en alle dag-IDF's op NHI-server produceren en kwalificeren.
