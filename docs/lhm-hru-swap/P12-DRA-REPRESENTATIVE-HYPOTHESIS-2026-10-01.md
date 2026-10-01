# DRA representative-cell provenance hypothesis — 2026-10-01

Base head: cdb796e6ee325d2ef8c052fadd796b0e58140674.

## Result

SINGLE_CURRENT_REPRESENTATIVE_CELL_AS_GENERAL_49RUN_RESISTANCE_EXPLANATION_FALSIFIED.

The broad negative all-member diagnostic prompted a separate test of whether
the realized resistances instead came from the current Runs representative
raster cell. This is a provenance hypothesis, never a production proposal.

For all 49 run IDs, read col,row from the recovered current workbook execution
representation, convert Fortran 1-based indices to zero-based raster indices,
sample the same native conductance and infiltration-factor grids used in the
previous diagnostic, and compute 62500/CDR and 62500/(CDR*INF).
Apply resistance bounds [1,100000], the >20000 deactivation rule and integer
serialization. No nature override was included: this deliberately isolates
the coordinate/support hypothesis. Its omission prevents interpreting individual
system-4 differences as a qualified nature result; the general hypothesis is
already falsified by widespread system-1..3 discrepancies.

| Field | Matches | Total |
| --- | ---: | ---: |
| DRARES | 10 | 245 |
| INFRES | 106 | 245 |

INFRES includes default/deactivated values and systems 4/5 with zero
infiltration factors. Those matches do not independently identify provenance.

Source inspection also confirms that supplied v0.38 fills member col,row
from each original HRU member SVAT, and its active aggregation loops include
all members. There is no active representative-cell substitution in these
loops. This is supplied-source semantics; it does not prove which executable
or input versions generated the archive.

The modern all-member authority, full 62500 m2 support, representative-SVAT
dqsat, 75 preregistered L differences and existing four qualified SWALLO
residuals remain unchanged. No new intentional differences or admissions.

Evidence: docs/evidence/2026-10-01/dra-representative-resistance-hypothesis.json.
Input hashes accompany the cases. The temporary SQLite only represents the
already qualified cached workbook state.

Next useful gate requires binding historical native input versions to the
realized executable. Repeated coordinate/support guessing cannot grant
DIRECT_DRA_PRODUCER_ADMITTED.
