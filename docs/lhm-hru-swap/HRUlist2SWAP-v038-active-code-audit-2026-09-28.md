# HRUlist2SWAP v0.38 active-code audit — 28 September 2026

Status: **SOURCE-BOUND; MAPPING ISSUES IDENTIFIED**

This audit treats active statements as authority over comments/history text.

## Irrigation threshold

History for v0.37 says irrigation is enabled when 30% of cells irrigate, replacing 50%. Active v0.38 code uses:

`if av > 0.37 then irr_switch_maj=1`.

Therefore the executable source threshold is 37%, not 30%. This is either an undocumented later change or a source/history inconsistency. Modern mapping must configure and test the threshold explicitly.

## Bottom boundary

v0.38 computes `qq`, FLF and QLAT for the selected water-boundary members, but active `.bbc` output writes only `qq` as `QBOT2`.

The alternatives using FLF and FLF+QLAT remain commented. Thus earlier history entries about qflf/qlat do not describe the active v0.38 bottom-flux mapping.

Active `qq` is based on `(head_l2-head_l1)/c1`, averaged over selected members and converted to cm units.

## Representative override ordering

Majority soil/land-use/root-depth values are calculated first. When a representative file exists, v0.38 later overwrites BFE, land use and root depth with representative values. Any quantities calculated before that overwrite must be checked for stale dependence.

`SWETR` is one known candidate: it is derived from earlier land-use state and is not visibly recomputed after representative land use is installed.

## Drainage versus selected water-boundary members

Bottom-boundary and meteorological aggregation use the selected `issvatwb` population. Active drainage sections do not consistently follow that same selection; comments and commented conditions show development history rather than one uniform policy.

## Canonical consequence

The modern HRU→SWAP contract should version each target quantity independently with:

- source field/product;
- member population;
- aggregation;
- representative override;
- threshold;
- unit conversion;
- fallback;
- mapping version.

Do not use program version alone as sufficient scientific mapping provenance.
