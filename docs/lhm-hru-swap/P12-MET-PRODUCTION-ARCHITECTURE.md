# P12 MET production architecture

Inputs are separated by responsibility.

STATIC:
- HRU membership and representation areas;
- HRU -> sparse 1 km meteo-pixel weights;
- 250 m NHI_regio district map -> meteo_maj;
- source hashes/provenance.

DAILY GRID:
- precipitation raster;
- ETref/evaporation raster.

DAILY DISTRICT:
- RAD, Tmin, Tmax, HUM, WIND, WET for 33 districts;
- daily maximum WET derived once.

COMPOSE:
- aggregate RAIN/ETref from sparse weights;
- lookup district meteorology;
- apply rainfall-duration consistency policy;
- emit typed MetRecord plus provenance.

RENDER:
- write SWAP .met text only;
- no scientific transformation in renderer.

Validated:
- district majority: 49/49 realized 1971 HRUs;
- WET policy: 17,885/17,885 realized rows explained;
- sparse aggregation algebra: unit tested and equivalent to member-wise area weighting.

Pending independent realized-output gate:
- RAIN/ETref, because supplied realized runs are 1971 and supplied daily grids are 2018.

The pending gate does not block implementation but blocks claiming full MET historical reproduction.
