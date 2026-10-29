# Direct HRU CSV route: identity stage

The identity stage reads neither SQLite nor the workbook Runs sheet.
`tools/swp_hru_authority.py` resolves soil from the HRU CSV, and landgebruik22
from that CSV if present, otherwise from precisely its representative SVAT.
Soil classification uses the canonical P12 lookup. No majority choice is made.
The result is an identity manifest, not SWP output or hydrological qualification.

Windows CMD, from the repository root with the existing qualified SVAT export:

```cmd
E:\tools\deltaforge\deltaforge_4\python.exe tools\swp_hru_authority.py --hru export_HRUschema_10242.csv --svat docs\evidence\2026-10-19-work-b\interfaces\SVAT_QUALIFIED.csv.gz --soil config\p12\bodem370_classification_lookup.csv --crop config\swp\soil2_landuse_crop.csv --output swp_identity
```

Python standard library only. Duplicate identities, conflicting aliases, missing
lookups and unexpected population size fail explicitly. Source and output hashes
are recorded. The crop lookup was extracted from the standalone lu2crop sheet of
Datamodel_10242.xlsx; it is independent of Runs and must remain reviewable.

Real-data check on 2026-10-29 resolved all 10,242 HRUs using the recovered
export_HRUschema_10242.csv and qualified 427,656-SVAT export. Four targeted tests
check authority precedence and ambiguous/missing representative rejection.

## Remaining physical inputs

The recovered extended HRU CSV has bodem370 and svat_repr but no representative
root depth or initial groundwater level. Do not fill these from old Runs contexts.
The historical control file references BasicData/csv/export_HRUschema_10242_copy.csv
(the five-column representative schema), BasicData/grids/rootzone_m.asc,
BasicData/grids/ahn_f250_m.asc and BasicData/modflow heads. Verify these actual
server sources and units before connecting physical context generation.
Historical GWLI uses member-average head minus ground elevation, converted to cm
and limited to nonpositive values. This is separate from representative soil and
land use. Representative root depth must follow the selected HRU representation.
Neither GHG nor a crop lookup is an implicit substitute for these physical inputs.
The existing modern_swp renderer remains the intended rendering backend.
