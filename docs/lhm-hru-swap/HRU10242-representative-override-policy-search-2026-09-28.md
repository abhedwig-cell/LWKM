# HRU10242 representative-override policy search — 28 September 2026

Status: **PATTERN LOCALIZED; EXACT PRODUCER RULE OPEN**

The 2,559 HRUs whose `_copy` schema sets `rz_repr`, `bfe_repr`, and `bodem_repr` to `-999` were compared with the other 7,683 HRUs using the authoritative HRU schema.

## Strongest observed pattern

The disabled group consists disproportionately of small HRUs:

- median member count: about 9 SVATs versus about 26 in the enabled group;
- about 65% of disabled HRUs contain fewer than 10 SVATs;
- the disabled set is not exactly equal to the rule `n_svat < 10`.

The group also differs in clustering/rest-group characteristics, consistent with HRUs produced through later aggregation/relaxation or donor handling rather than the primary well-populated cluster path.

## Negative findings

No exact one-column rule was found based only on:

- HRU size;
- representative-SVAT availability;
- one soil/land-use field;
- one MAE/RMSE field.

Therefore the 2,559 rows must not be canonicalized as a guessed threshold rule.

## Working interpretation

The `_copy` file is best treated as a production policy artifact that disables representative soil/root-zone values for a subset associated strongly with small/rest-group HRUs. The exact producer of that policy remains to be found, likely in historical HRU/NRU schematisation or a post-clustering preparation script.

Canonical modernization should preserve the observed boolean decision first, while separately recovering or redesigning its scientific rule.
