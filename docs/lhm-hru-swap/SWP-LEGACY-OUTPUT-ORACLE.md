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

## Confirmed unwanted side effects

run_000000012 contains:
- 12.met: 0 bytes
- 12.dra: 0 bytes
- 12.bbc: 0 bytes
- gras_maaien.crp: copied asset
- atmospheric_1975-2020.co2: copied asset
- swap.swp

Thus the legacy generator creates/copies auxiliary files even when the run-specific MET/DRA/BBC files contain no data. The replacement must not reproduce this behavior by default.

## Resolved hidden rule

ELAS is concretely observed as 1e-6 in generated hydraulic rows. This may be a SWAPtools default/template rule; provenance inside SWAPtools is still open, but output semantics are now bound.

RDS is observed as 120 cm across the generated sample and does not follow the simple values previously seen in Runs/Wortelzone. Its derivation still requires recovery; historical regression should use realized output until the rule is identified.

## Regression oracle policy

These generated SWP files are primary realized-output evidence for renderer equivalence. Compare semantic assignments/tables first; byte equality is secondary because whitespace/template comments are not scientific behavior.
