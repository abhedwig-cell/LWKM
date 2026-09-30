# P12 schema-first static HRU model

The modern static producer is intentionally split into authoritative and derived fields.

AUTHORITATIVE REPRESENTATION (Piet HRU schema):
- representative_svat
- representative_bfe
- representative_soil
- representative_root_depth
- representative_landuse (resolved through representative_svat if not explicit)

DERIVED FROM REPRESENTATIVE LAND USE:
- swetr
- is_nature
- crop mapping
- any land-use-dependent drainage switch

INDEPENDENT HRU AGGREGATES:
- meteo district: all-member category majority
- irrigation: calibrated >0.37 member fraction then irrigated-type majority
- uopp totals: sum of active SVAT area on relevant membership
- glk/hh/coordinate diagnostics as explicitly declared
- drainage equivalents: all-member MODFLOW support
- BBC: selected source-cell support

QA ONLY WHEN SCHEMA PRESENT:
- raster-member majority land use
- raster-member majority bfe
- legacy RDS candidate calculation

No QA field may overwrite authoritative representation.

## Dependency ordering

1. load and validate schema;
2. resolve representative SVAT attributes;
3. derive all representation-dependent flags;
4. compute independent aggregations;
5. compute producer outputs;
6. render files.

This ordering prevents the legacy bug class where a derived flag is calculated before an authority override.
