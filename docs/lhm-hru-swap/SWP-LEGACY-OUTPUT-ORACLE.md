# Legacy SWAPtools realized-output oracle

Source: user-generated run_000000012.zip, produced by the legacy R scripts. Despite the archive name it contains 14 run directories (run_000000001 through run_000000014).

## Direct observations

For the inspected generated SWP files:
- TSTART = 1971-01-01
- TEND = 2021-12-31
- RDS = 120.0 cm
- ELAS = 0.000001 in hydraulic rows
- METFIL is run-specific (<run_id>.met)
- DRFIL is run-specific (<run_id>)
- BBCFIL is run-specific (<run_id>)
- SWDRA = 1
- SWBBCFILE = 1
- SWBOTB = 2

Crop rotation is expanded into explicit yearly rows in the SWP; for run 12 these reference gras_maaien.

## Auxiliary lifecycle correction

run_000000012 initially contains zero-byte 12.met, 12.dra and 12.bbc targets. User domain knowledge establishes that substantive content for files such as MET and BBC is generated later by the Fortran workflow. These zero-byte files are therefore intermediate lifecycle targets/placeholders, not evidence that the auxiliary input is semantically empty.

The replacement must preserve the producer contract while avoiding unnecessary regeneration. SWP rendering and auxiliary-content production remain separate stages.

## Resolved hidden rule

ELAS is concretely observed as 1e-6 in generated hydraulic rows. This may be a SWAPtools default/template rule; provenance inside SWAPtools is still open, but output semantics are now bound.

RDS is observed as 120 cm across the generated sample and does not follow the simple values previously seen in Runs/Wortelzone. Its derivation still requires recovery; historical regression should use realized output until the rule is identified.

## Regression oracle policy

These generated SWP files are primary realized-output evidence for renderer equivalence. Compare semantic assignments/tables first; byte equality is secondary because whitespace/template comments are not scientific behavior.
