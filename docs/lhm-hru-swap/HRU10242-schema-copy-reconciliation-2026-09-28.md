# HRU10242 schema-copy reconciliation — 28 September 2026

Status: **SEMANTIC COPY CONFIRMED; THREE FIELDS ALTERED**

Compared current artifacts `export_HRUschema_10242.csv` and `export_HRUschema_10242_copy.csv`. Both contain 10,242 rows and 43 columns.

Exactly three columns differ: `rz_repr`, `bfe_repr`, and `bodem_repr`. All other 40 columns are identical. `svat_repr` itself is unchanged.

For 2,559 HRUs, the copy replaces the three representative values by `-999`. For the other 7,683 HRUs they remain identical to the authoritative schema.

Correction, 20 October 2026: the earlier interpretation that `bfe_repr > 0` controls the override is superseded by the [active-code audit](HRUlist2SWAP-v038-active-code-audit-2026-09-28.md) and `config/swap-mapping/HRU10242-v038-reconstruction.yml`. The supplied v0.38 source applies `bfe_repr` and `rz_repr` whenever the representative file exists. It does not define `-999` as a disable switch. The observed copy edit is confirmed; its intended operational effect and the executable used historically are not established by that edit alone. Preserve the distinction between source semantics, actual historical execution and modern policy.

The copy must not be treated as an interchangeable duplicate. A modern explicit override policy requires its own scientific decision and qualification. The recovered clustering reference in `csv.zip` has 36 columns and is a separate artifact from these enriched 43-column variants; the complete enrichment producer remains an open Work B source binding.
