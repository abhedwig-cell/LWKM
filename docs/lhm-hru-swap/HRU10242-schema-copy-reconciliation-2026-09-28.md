# HRU10242 schema-copy reconciliation — 28 September 2026

Status: **SEMANTIC COPY CONFIRMED; THREE FIELDS ALTERED**

Compared current artifacts `export_HRUschema_10242.csv` and `export_HRUschema_10242_copy.csv`. Both contain 10,242 rows and 43 columns.

Exactly three columns differ: `rz_repr`, `bfe_repr`, and `bodem_repr`. All other 40 columns are identical. `svat_repr` itself is unchanged.

For 2,559 HRUs, the copy replaces the three representative values by `-999`. For the other 7,683 HRUs they remain identical to the authoritative schema.

This is operationally significant. HRUlist2SWAP v0.38 reads these fields from `HRU2SVAT_repr_csv` and only applies the representative soil/root-zone override when `bfe_repr > 0`. The copy therefore deliberately disables that override for 2,559 HRUs while retaining the representative SVAT relation and all other schema fields.

The copy must not be treated as an interchangeable duplicate. Modernization should replace this sentinel edit with an explicit policy field such as `use_representative_soil_rootzone`, plus a reason/policy identifier.
