# Falsification test for `export_HRUschema_10242_copy.csv`

Status: **REQUIRED BEFORE PRODUCTION-AUTHORITY CLAIM**

The `_copy` artifact contains 2,559 rows with `rz_repr=bfe_repr=bodem_repr=-999`, while the supplied v0.38 source unconditionally applies representative `bfe_repr` and `rz_repr` when the file exists. Literal execution would make these values invalid, including an eventual negative array index in `bodem2bofek(bfe_maj)`.

## Required direct test

For the 2,559 affected HRUs, join:

- `export_HRUschema_10242.csv`;
- `export_HRUschema_10242_copy.csv`;
- `SVAT2SWAP10242.csv`;
- `Bodem370_2_bofek2020.csv`;
- HRU member data needed to reconstruct majority soil/root depth.

Compare realized run-table fields:

- `bodem_id`;
- `RDS`;

against candidates:

A. original representative schema (`bfe_repr`, `rz_repr`);
B. all-member/majority fallback;
C. another deterministic mapping if evidenced.

## Decision logic

- exact match to A → `_copy` was not the effective input, or sentinel rows were repaired before execution;
- exact match to B → production path had an undocumented fallback not present in supplied source;
- neither → locate additional transformation/executable divergence.

Do not infer intent from the `-999` sentinel itself.
