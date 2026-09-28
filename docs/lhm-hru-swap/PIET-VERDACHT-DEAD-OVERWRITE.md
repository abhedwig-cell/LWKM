# Suspicious-cell semantics: eight flags are authoritative in LWKM_makeHRU v0.20

A source audit resolves the relationship between Piet_verdacht.asc and the eight explicit selection grids.

LWKM_makeHRU reads verdacht_asc (configured as LHM_uitvoer/filter/Piet_verdacht.asc) and initially executes:

IF (verdacht(ii,jj).GT.0) plotlist(kk)%isuit(ll)=1

However, immediately after reading the eight individual selection values, the program executes:

plotlist(kk)%isuit(ll)=0

and then reconstructs isuit entirely from ghg_sel, gt1_sel, gt2_sel, gt8_sel, kwel_sel, wegzijging_sel, runoff_sel and subinfil_sel.

Therefore the earlier Piet_verdacht assignment is overwritten. In v0.20 it does not contribute to the final isuit value used for valid/suspicious SVAT separation.

The broader producer raster Piet_verdacht is itself piet_sel + verdachte_cellen, where verdachte_cellen uses additional class-based criteria. Those broader criteria are therefore diagnostic/legacy in the audited v0.20 path, not part of the final eight-flag qualification.

Canonical consequence: do not make Piet_verdacht a scientific dependency of B qualification. Retain it only as optional historical diagnostic evidence.

Historical regression target 20,934 must be tested against the union of the eight explicit flags, not against Piet_verdacht.
