# P12 realized MET district oracle

Supplied meteo.zip contains 33 historical district/station time-series families:
  1.xxx .. 33.xxx
including 1971 files used by the supplied realized runs.

It does NOT contain the integer spatial meteo district grid referenced by control parameter 'meteo'.

## Oracle strategy

For each realized HRU .met:
1. ignore RAIN and ETref initially;
2. compare RAD, Tmin, Tmax, HUM, WIND and WET against all 33 district series on matching dates;
3. identify the district with exact/rounding-compatible agreement;
4. use multiple dry and wet days so WET repair does not make identification ambiguous;
5. persist inferred district id and confidence.

This independently validates the executable's district lookup without requiring the missing district map.

## Source-current semantics

The supplied Fortran samples the integer meteo grid per SVAT and sets:
  meteo_maj = MAJORITY(meteo_i)
over all HRU members.

Thus district selection is member-count majority on the 250 m source-cell population.

## WET caution

WET cannot be used alone for station identification because output modifies it:
- rain < 0.01 -> WET=0;
- rain >=0.01 and district WET<0.01 -> replace by max WET across all districts, minimum 0.01.

RAD/Tmin/Tmax/HUM/WIND are direct district fingerprints and are preferable for oracle matching.
