# Soil preprocessing regression

Full realized authority: csv.zip/csv/SVAT_INFO_HRU.CSV, 427,656 SVATs.

Results:
- 365 bodem370 classes occur in the realized SVAT population.
- Each observed bodem370 maps to exactly one tuple (bofek79,pawn21,grondsoort4,grondsoort2): zero ambiguity.
- Bodem370_2_bofek2020.csv contains 370 source classes; five (14,142,143,197,198) do not occur in the realized SVAT population.
- Comparing realized bofek79 with Bodem370_2_bofek2020.csv yields 10 differing bodem370 codes:

| bodem370 | realized bofek79 | BOFEKnhi79 |
|---:|---:|---:|
|78|40|39|
|79|39|40|
|81|39|44|
|82|44|39|
|94|31|28|
|95|28|31|
|147|46|41|
|148|41|46|
|170|44|39|
|171|39|44|

These differences are not to be silently normalized. They may represent a BOFEK mapping version difference, manual correction, or ordering issue. Historical compatibility uses the realized mapping until provenance is resolved.

Further aggregation is strictly deterministic in the realized data:
- every bofek79 maps to one pawn21;
- every pawn21 maps to one grondsoort4;
- every grondsoort4 maps to one grondsoort2.

Therefore the target preprocessing can be represented as versioned tabular mappings rather than four separate ASCII rasters.
