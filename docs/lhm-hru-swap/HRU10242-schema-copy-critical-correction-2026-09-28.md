# Critical correction: HRU10242 `_copy` sentinel interpretation — 28 September 2026

Status: **PREVIOUS DISABLE-OVERRIDE INTERPRETATION WITHDRAWN**

Earlier reconstruction interpreted `bfe_repr=-999` as an intentional switch that disabled representative soil/root-zone override. Reinspection of the supplied HRUlist2SWAP v0.38 source does not support that interpretation.

## Source behaviour

When `HRU2SVAT_REPR_CSV` exists, v0.38 sets `isrepr=.TRUE.` and reads all representative fields. Later, for every HRU, it unconditionally executes the equivalent of:

- `bfe_maj = bfe_repr`;
- `lgn_maj = LGN(svat_repr)`;
- `rds_maj = rz_repr / 100`.

No `bfe_repr > 0` guard is present in the inspected supplied source around this override.

The run table later indexes `bodem2bofek(bfe_maj)`. A literal `bfe_maj=-999` would therefore be invalid/out-of-bounds in ordinary Fortran execution rather than a clean fallback to majority soil.

## Consequence

The 2,559 sentinel rows in `export_HRUschema_10242_copy.csv` cannot currently be classified as a source-defined “disable representative override” policy.

Possible explanations that remain to be tested include:

1. `_copy` was not the exact file used for the observed successful run table;
2. the production executable differs semantically from the supplied v0.38 source despite matching version identity;
3. another preprocessing/edit step replaced sentinel values before execution;
4. bounds/runtime behaviour or another hidden mapping changed the effective path;
5. the file is an experimental/manual artifact rather than valid production input.

Until resolved, `_copy` is an **observed artifact with unsafe sentinel semantics**, not canonical policy authority.

The prior documentation claiming that `-999` deliberately disables representative override is superseded by this note.
