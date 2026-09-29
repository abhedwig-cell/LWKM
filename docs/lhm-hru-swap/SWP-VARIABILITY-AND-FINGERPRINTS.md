# SWP variability audit from 14 realized legacy runs

Oracle: run_000000012.zip contains generated SWPs for runs 1..14.

The generated SWPs are highly similar. Variability is concentrated in a small set of semantic dependencies rather than requiring a separate procedural generation workflow per run.

## Dependency classes

Global configuration:
- simulation period and most switches/constants;
- output settings;
- common model options.
These should be one versioned renderer/template configuration.

Run references:
- run-specific file stem used by METFIL/DRFIL/BBCFIL in the legacy output.
These references should only exist when the corresponding external file is actually required.

Soil profile:
- discretisation rows (ISUBLAY, ISOILLAY, HSUBLAY, NCOMP).

Soil hydraulics:
- retention/conductivity parameters plus BDENS and observed ELAS=1e-6.

Soil texture:
- PSAND, PSILT, PCLAY, ORGMAT.

Crop/rooting:
- RDS and crop-rotation rows/file references.

Bottom boundary:
- SWBOTB and DATE2/QBOT2 series where SWBOTB=2.

## Incremental implication

A change in one dependency does not justify rebuilding unrelated shared assets. The cache records separate hashes for global, soil_profile, soil_hydraulics, soil_texture, rooting, bottom and run_refs, plus one effective fingerprint.

This also makes change explanations possible, e.g.:
- HRU 4818 regenerated: soil_hydraulics changed
- HRU 4819 skipped: no effective dependency changed
- HRU 4820 regenerated: rooting changed

The target generator does not use output timestamps as freshness authority.
