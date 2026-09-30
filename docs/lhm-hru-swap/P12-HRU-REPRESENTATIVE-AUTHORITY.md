# P12 HRU representative authority contract

## Authority

For the current 10,242-HRU production path, representative HRU land use, soil/profile and rooting information are authoritative from Piet's HRU schema:
  export_HRUschema_10242_copy.csv
configured as:
  HRU2SVAT_REPR_CSV.

Do not recompute these representative choices from member rasters in the modern producer.

## Authoritative fields / derivation

Current legacy reader provides per HRU:
- svat_repr
- rz_repr
- bfe_repr
- bodem_repr

Legacy then sets:
- bfe_maj = bfe_repr
- lgn_maj = lgn(svat_repr)
- rds_maj = rz_repr / 100

Modern code must model these as representative HRU attributes, not variables named *_maj.

Where land-use code is not directly present as a schema column, resolve it through the schema-selected svat_repr against the immutable source SVAT attributes. This is lookup/provenance, not a new majority decision.

## Role of member-raster majorities

Legacy calculations of lgn_maj, bfe_maj and rds_maj before representative override are:
- historical fallback behavior when no HRU schema is available;
- QA diagnostics against the authoritative schema;
- NOT production authority when HRU2SVAT_REPR_CSV is present.

## RDS control-flow defect scope

The confirmed inside-loop fallback defect in legacy rds candidate selection remains a real code defect.

For the current configured 10,242 path it is subsequently overwritten by:
  rds_maj = rz_repr / 100
when representative schema input exists.

Classification:
  DEFECT_CONFIRMED_CONTROL_FLOW_BUT_OVERRIDDEN_IN_CURRENT_REPR_MODE.

Modernization:
- do not port defective loop into normal production path;
- retain a legacy-fallback regression only if schema-absent mode remains supported;
- production path must fail clearly if authoritative HRU schema is required but missing, rather than silently re-deciding HRU identity.

## QA

Compare raster-derived modes against schema attributes and report disagreements, but never use QA result to silently replace schema authority.
