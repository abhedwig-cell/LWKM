# MET07: verkeerde FG-HUM-toewijzing bewezen, UG-herstelproef gereed

## Ontvangen bewijs

MET_HUM_BRONBEWIJS.zip, SHA256 1fc6ac9edfc95f5ebd54de1434d95a29c4c4b7a3010f6a1fbb24419cb9915507, is volledig lokaal geopend. De 16 opgenomen bronbestanden zijn gehasht en komen overeen met het meegeleverde register. De daadwerkelijke start_meteo.cmd roept w09_direct_met.exe aan met w09_met_config.ini. Dit onderscheidt de actieve aansturing van het eveneens aanwezige w09_config.ini.

De actieve configuratie heeft SHA256 991cbcb82f77fdb519496ca1344c5c38d56d0d08d200279cdb65c8376d636070. Zij bindt path_FG aan meteo/FG/FG_{date}.asc met scale_FG=1. De producerbron op de door README_SERVER.txt genoemde commit b6299f9817b527be798abc349d18b8ad9820c2d3 is opnieuw gelezen: tools/native/w09_met05/src/w09_direct_met.cpp, Git-blob dff2def188f53a0cf50dbcbdb9b2f90c86cc9053. De bron schrijft v[5], afkomstig uit FG, naar HUM.

De executable is niet opnieuw onafhankelijk uit deze bron gebouwd. Naast de gerapporteerde bronbinding is de fout daarom rechtstreeks op waardeniveau gereproduceerd:

| HRU | Datum | Oude HUM / gereproduceerde FG, zes decimalen | UG als HUM, kPa | WIND blijft |
|---|---|---:|---:|---:|
| 1 | 1970-01-01 | 3.600000 | 0.263000 | 3.586050 |
| 1 | 1970-02-20 | 10.300000 | 0.724000 | 11.595999 |

Alle 18 HRU-1-meteogewichten zijn gebruikt zonder normalisatie. Hun som is 0.9999999999999998. Geen NoData/donor nodig voor deze twee bronproeven. De gewichtenbron is gebonden aan SHA256 6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c.

## Bronbetekenis, niet alleen een bereiktoets

Het oorspronkelijke run-lokale mete_grid.inp heeft SHA256 baf22e8a30e429995f4b3623f3cceac89c56cb9dd983cf5c86887a4f70421d1f. Alle 3653 records zijn gelezen: veld 10 verwijst naar UG; veld 11 naar FG. Het document Rapport_Koppeling_SWAP4_en_MODFLOW6_V03.docx, Bijlage D, Meteo, benoemt file_wind=FG en file_hum=UG en specificeert luchtvochtigheid in kPa. De publieke MetaSWAP-inputreferentie bevestigt humgrid in kPa: https://nhi.nu/documents/49/MetaSWAP_Report_913_3_V8.1.1.4.pdf, sectie METE_GRID.INP. PDF-tekst is opgehaald; web-screenshot faalde met cache miss. De exacte toewijzing wordt tevens door het private koppelrapport gedragen.

Deze LHM-UG-rasters zijn modelinvoer voor dampdruk, niet de ruwe KNMI-kolom UG met relatieve vochtigheid. Geen deling door tien, afkapping, nieuwe temperatuurafleiding of nulvulling. De correcte bronregel is expliciet path_HUM=meteo/UG/UG_{date}.asc, actual_vapour_pressure, kPa, schaal 1.

## Geleverde herstelroute

LWKM_MET07_HUM_Herstel_Proef_v01.zip: 1214865 bytes, SHA256 704b27457b370c329d164e62190637c3e6c52f932bb5785502280e58786739ae.

- tools/met_hum_repair.py: SHA256 7165934f3de63585ab357260fafee106caafa42f37edf0222ed09e6affe93e1f.
- run_hum_trial.py: SHA256 7c42a38a9e5955c929e63b30cd0cca27f95ed3f10a875298d47a05c30d165c2e.
- Lokaal auditrapport LWKM_MET_HUM_Bronconclusie_20261116.json: SHA256 d027800aa1e42e2bb83d6c436ed23cc8942e20550fdf0c2ce2b48959b437455f.

Het pakket leest uitsluitend de UG-rasterreeks opnieuw, voor dezelfde zes proef-HRU's: 1,3,181,7870,7871,7929. Het verifieert de reeds ontvangen catalogi, bronconfiguratie, gewichten, runcontrol en twee rasterankers. Per dag worden bronhash en eventuele dichtstbijzijnde-geldige donor vastgelegd. Gewichten worden niet aangepast. Onjuiste grootheid, schaal, geometrie, ontbrekende dagen, niet-eindige waarden en HUM buiten 0..10 kPa worden geweigerd.

Alleen het HUM-token in nieuwe MET-afgeleiden verandert. Alle overige tokens, datums, witruimte en regeleinden worden op bytegelijkheid gecontroleerd. SWP/DRA/BBC/CRP/CO2 blijven ongewijzigd. Oude kandidaatmappen en MET06-uitvoer blijven intact. Daarna start dezelfde SWAP 4.3.1 met de al gemeten executablehash d13f5e0321db1780d211520287dc59db2e7aa763649998a4b29a187195ca89a5. Geen ingekorte periode. Normale eindmelding, passende exitcode, einddatum, dagelijkse eindige CSV en invoerintegriteit blijven vereist. Stop bij eerste fout.

## Uitvoering en kwalificatie

Vanuit de pakketmap in CMD: HERSTEL_HUM_EN_START_PROEF.cmd.
Terugrapport: LWKM_tools/LWKM_MET07_HUM_Herstel_Proef_v01_resultaat/MET_HUM_PROEF_TERUG.zip. OPEN_RESULTAAT.cmd opent die map.

59 lokale unittest-tests slagen, ook opnieuw uit de definitieve ZIP: 28 bestaande runner-tests plus 31 nieuwe kern-/bron-/integratietests. Echte twee-dagen-bronreplay is inbegrepen; modelprocesproeven gebruiken een synthetisch proces, geen echte SWAP. Python-3.8-grammatica is gecontroleerd. De Windows-starter, volledige UG-reeks en nieuwe SWAP-proeven zijn hier niet uitgevoerd.

Dit is een beperkte herstelproef, nog geen landelijke MET-correctie of productievrijgave. De oude MET06-productie mag wegens de verkeerde bronsemantiek niet als correcte HUM-invoer worden aangemerkt. Andere meteovariabelen worden niet automatisch opnieuw gekwalificeerd. Geen nieuw LHM-waterbalansonderzoek.

Deze commit bevat de bewijs- en overdrachtsnotitie. De poging om de numerieke module als nieuw Git-bestand te schrijven faalde met een RemoteProtocolError; een daaropvolgende fetch vond dat bestand niet. De werkelijk geteste nieuwe broncode en tests staan daarom in de ZIP en zijn nog niet als losse bestanden in Git geintegreerd. Geen merge naar main.
