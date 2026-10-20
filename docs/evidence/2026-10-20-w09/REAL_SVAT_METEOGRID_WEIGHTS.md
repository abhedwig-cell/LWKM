# W09 real SVAT-to-meteogrid weight build, 2026-10-20

Actuele aanvulling D1: de projecteigenaar heeft area_svat(3).inp inmiddels als W09-authority bevestigd. Het onderstaande eerdere oppervlakteblokkeringslabel is historisch en niet meer actief. Zie docs/production/W09_SVAT_AREA_AUTHORITY_DECISION_2026-10-20.md en de D1-evidence voor byte-identieke herhaling.

## Supplied real inputs
- `export_svat_HRU_NRU_10242(4).csv`: SHA256 `13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319f7f4`
- `area_svat(3).inp`: SHA256 `352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc`
- `precipitation_19700101.asc`: SHA256 `bbf423df8513b3b46779c96bad12f850fa6f7b0df0f9f5d99c1a5fd92dc3375e`

The first CSV supplies 427656 unique SVAT IDs, the 10242 HRU memberships, and x/y coordinates. In area_svat.inp the first token is SVAT ID and the second is nominal SVAT area in m²; the remaining columns are not needed for this producer. All selected SVATs joined exactly once; no missing areas.

## Actual calculated candidate
Grid: 300x325 at 1000 m; origin x=0, y=300000. Sum SVAT areas to each HRU+grid-cell combination, divide by total HRU original SVAT area.
- 427656 selected SVATs;
- 10242 HRUs;
- 277190 unique HRU-to-meteogrid links;
- max |sum weights - 1| = 7.66e-15;
- independent numeric regression with a deterministic synthetic grid against direct original SVAT area weighting: max absolute error 5.996e-15.
- generated `hru_meteogrid_weights.csv` SHA-256 `6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c`.

## Qualified exception / blocker
The supplied area_svat.inp sums to **25,514,516,032 m²** over the selected SVATs, whereas Work B's previously bound source `SVAT_INFO.csv`/snapshot had **25,511,141,709 m²**, a **+3,374,323 m²** difference. These are not automatically interchangeable scientific authorities. Keep weights as a reproducible source-specific candidate until the cause is reconciled, and do not overwrite the qualified Work B area authority without an explicit decision.

The large original source files and candidate CSV are stored in the conversation exchange, not embedded into Git; hashes and algorithm/procedure belong in Git. Attach the generated output through the normal Q4 transfer or release path. No MET production admission is claimed.
