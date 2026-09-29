# BOFEK mapping discrepancy impact

The ten bodem370 -> BOFEK differences between the realized SVAT table and Bodem370_2_bofek2020.csv are treated as a mapping-version discrepancy.

The differences form several apparent swaps or reassociations:
- 78/79: 40/39 versus 39/40
- 81/82: 39/44 versus 44/39
- 94/95: 31/28 versus 28/31
- 147/148: 46/41 versus 41/46
- 170/171: 44/39 versus 39/44

This pattern is more consistent with an alternative mapping/version or source-code ordering than with independent random cell edits. That interpretation remains a hypothesis until an older producer table/script is recovered.

Historical compatibility authority remains the realized SVAT mapping.

Do not replace realized BOFEK values with the supplied BOFEK2020 lookup merely because the latter appears newer or cleaner. Quantify affected SVATs and downstream PAWN/ground-type changes before considering a modern mapping update.
