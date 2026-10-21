# W09 serverbronlocaties WIND en WET_RAW

Datum: 2026-10-21
Status: locatie door projecteigenaar vastgesteld, daadwerkelijke serverdekking nog te verifiëren.

De twee aanvullende dagelijkse ASCII-meteorasterfamilies worden geplaatst onder de bestaande LHM 4.3.3-meteoroot:

- `E:\LHM_4.3.3\Data\2_Model_Input\meteo\WIND`
- `E:\LHM_4.3.3\Data\2_Model_Input\meteo\WET_RAW`

De overige LHM-meteorasterfamilies blijven onder dezelfde `meteo`-root. De WIND-velden bevatten windsnelheid op 10 m in m/s; WET_RAW bevat de ruwe positieve KNMI-neerslagduur als dagfractie of NODATA. WET_RAW is **niet** de definitieve SWAP WET.

Bij SWAP-MET-productie: LHM-neerslag 0 => WET 0; neerslag > 0 en geldige positieve raw duur => die duur; neerslag > 0 en geen geldige positieve duur => WET 0.1. Gebruik vaste HRU-gridgewichten op basis van `area_svat(3).inp`; bij ontbrekende rasterpixels de dichtstbijzijnde geldige rastercel. Controleer de ALTW/windmeethoogteinstelling in SWAP 4.3.1.

Voor productie nog te controleren: dagelijkse bestandsnamen, 1970–2022-dekking, eenheden, 300×325/1000m geometrie, NODATA, manifesten/hashes en reproduceerbare EXE/CMD-verwerking. De NHI-server heeft geen Python en geen internet.
