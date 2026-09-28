# Historical 57,880-SVAT donor layer — characterization

Date: 28 September 2026

Status: **OBSERVED LEGACY BEHAVIOUR, NOT CURRENT REPLACEMENT AUTHORITY**

Using the previously supplied `LHM2SWAP.zip`, `analyses/svat.csv` was compared row-by-row with `analyses/svat_cor.csv`.

## Exact result

- both tables contain 427,656 unique SVATs;
- 57,880 target rows change on at least one non-target field;
- every one of those 57,880 corrected rows can be matched exactly to the non-target properties of an existing row in the original `svat.csv`, excluding `svat`, `N` and `OPPHA`;
- therefore the legacy correction is demonstrably a donor-copy operation rather than an arithmetic adjustment of individual fields;
- target and donor have the same `lu2` in 100% of the 57,880 cases.

Using coordinates from the older `SVAT_INFO.CSV`, donor distance has median about 4.27 km, 75th percentile about 8.00 km, 95th percentile about 14.56 km and maximum about 292 km. Only about 70.4% of target/donor pairs remain in the same older `district` classification. This rules out a simple nearest-cell or same-district-only interpretation.

The older `isverdacht` field is not equivalent to the later qualification rules: only 6,642 of these 57,880 targets have the old `isverdacht=1`. Therefore these figures must not be used to infer the current 20,934 replacement algorithm.

## Interpretation

This strengthens the separation between three concepts:

1. pre-HRU hydrological replacement;
2. HRU clustering/rest-group donor matching;
3. final HRU representative SVAT.

`svat_cor.csv` is useful evidence for historical donor-copy semantics, but is not authority for the current pre-HRU `replacement_donor_svat` policy.
