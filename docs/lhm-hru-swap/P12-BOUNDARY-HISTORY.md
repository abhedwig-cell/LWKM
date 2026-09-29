# P12 boundary-condition history and priority

hrulist2SWAP source history records:
- v0.33: qlat + qflf combined as bottom boundary.
- v0.34: qflf restored as bottom boundary; infiltration disabled under a separate threshold rule.

Therefore qlat presence in current computations does not imply it is the active prescribed bottom flux in the current production configuration.

Audit priority:
1. identify which array is actually written as QBOT2 in the current branch/configuration;
2. bind FLF native MODFLOW unit/support and all prior scaling;
3. only then assess current BBC volume conservation;
4. audit QLAT separately as a coupling/water-balance diagnostic and historical alternative boundary component.

This history also means old commented qlat formulas may belong to superseded boundary experiments rather than simple bugs. Preserve them as provenance.
