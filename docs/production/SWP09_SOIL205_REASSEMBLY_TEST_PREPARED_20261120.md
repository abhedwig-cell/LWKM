# SWP09 bodem205: vervolgassemblage en SWAP-proef (voorbereid, niet uitgevoerd)

Ontwikkeld op 20 november 2026. Het pakket is **LWKM_SWP09_Soil205_Assemblage_En_Proef_v01.zip** (4.496.197 bytes, SHA-256 `01c199f4ae5d8efc51b47008fa9312245d5687ab1539d2e6b8533fec3593cfce`).

De pakketcode is als apart Windows-server ZIP geleverd, niet in deze Git-commit ingecheckt. De SWP-producentregel 204→205 staat wel als broncode in deze branch.

De oude assemblage v03 accepteerde alleen één gezamenlijk SWP/BBC-receipt. De nieuwe assemblage accepteert precies drie afzonderlijk gebonden ontvangsten: een **nieuw SWP09-swp-only** terugrapport, het behouden volledige **BBC10**-receipt en het bestaande **MET07**-receipt. Het controleert alle 10.242 individuele manifestrecords, een volledige runs_candidate.csv zonder bodem204, een geldige lijst van 204→205-vervangingen en specifiek 8532,8533,8534,8768. De SHA-256 van de pas op de NHI-server aangemaakte SWP09-receipt wordt bij assemblage bepaald en immutable in de nieuwe keten vastgelegd. DRA01 is ongewijzigd.

Nieuwe assemblage: `LWKM_rebuilds\SWAP_HRU_SWP09_BBC10_MET07_DRA01_Soil205_v01`. Nieuwe SWAP-campagne: `LWKM_rebuilds\SWAP431_Soil205_Proef_v01`. Start met `START_ASSEMBLAGE_EN_8532_PROEF.cmd`; assembler controleert eerst de hele populatie en voert dan uitsluitend **8532** uit, met timeout 14.400 seconden. Later kunnen 100 proef-HRU's worden uitgevoerd met `START_100_PROEFRUNS.cmd`. Nationale vervolgstart vergt succesvolle 100, expliciete approval en afzonderlijke CMD; geen automatische acceptatie of hergebruik van oude 99 geslaagde resultaten.

Lokale verificatie: 13 unit-tests plus 5 subtests geslaagd, uitgepakt pakket geeft `PACKAGE_HASHES_OK`. De landelijk nieuwe SWP09-receipt is **nog niet beschikbaar**; de tests gebruiken expliciet een synthetische SWP09-receipt afgeleid van de echt ontvangen oude nationale resultaten. Dat test de koppeling, niet de hydrologie. Geen NHI-aanroep of echte SWAP-berekening uitgevoerd. Geen nieuwe waterbalansacceptatie.

Aan de gebruiker geleverd als server-ZIP; na terugontvangst van de run moeten de drie gecorrigeerde bodemgevallen en eventuele nieuwe balansverschillen afzonderlijk worden beoordeeld.
