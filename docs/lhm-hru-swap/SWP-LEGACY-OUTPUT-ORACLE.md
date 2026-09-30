# Legacy SWAPtools realized-output oracle

Source set:
- user-generated `run_000000012.zip`, produced by the legacy R scripts. Despite the archive name it contains 14 run directories (`run_000000001` through `run_000000014`);
- loose realized `swap.swp` with matching `2000.bbc`, `2000.dra` and `2000.met`, recovered as raw bytes from Library on 2026-09-30.

## Direct observations from runs 1-14

For the inspected generated SWP files:
- TSTART = 1971-01-01
- TEND = 2021-12-31
- RDS = 120.0 cm in this 14-run sample
- ELAS = 0.000001 in hydraulic rows
- METFIL is run-specific (<run_id>.met)
- DRFIL is run-specific (<run_id>)
- BBCFIL is run-specific (<run_id>)
- SWDRA = 1
- SWBBCFILE = 1
- SWBOTB = 2

Crop rotation is expanded into explicit yearly rows in the SWP; for run 12 these reference gras_maaien.

## Independent realized run 2000 oracle

The loose `swap.swp` is internally identifiable as run 2000 because it references:
- `METFIL = '2000.met'`;
- `DRFIL = '2000'`;
- `BBCFIL = '2000'`.

Matching substantive `2000.met`, `2000.dra` and `2000.bbc` files are present as separate realized inputs.

Observed SWP values:
- TSTART = 1971-01-01
- TEND = 2021-12-31
- METFIL = 2000.met
- SWETR = 0
- SWINCO = 2
- GWLI = -47.0 cm
- PONDMX = 0.2 cm
- RSRO = 0.25 d
- RDS = 40.0 cm
- SWDRA = 1
- DRFIL = 2000
- SWBBCFILE = 1
- BBCFIL = 2000
- SWBOTB = 2
- NUMNODNEW = 43
- four observed hydraulic rows all contain ELAS = 0.000001.

This independent oracle falsifies any interpretation of `RDS=120` as a global SWAPtools default. The earlier 120 cm observation was a property of runs 1-14, not a universal renderer rule. RDS is therefore run-dependent and must be bound to an authoritative run/soil/crop derivation before admission.

## Auxiliary lifecycle correction

`run_000000012` initially contains zero-byte 12.met, 12.dra and 12.bbc targets. User domain knowledge establishes that substantive content for files such as MET and BBC is generated later by the Fortran workflow. These zero-byte files are therefore intermediate lifecycle targets/placeholders, not evidence that the auxiliary input is semantically empty.

The replacement must preserve the producer contract while avoiding unnecessary regeneration. SWP rendering and auxiliary-content production remain separate stages.

Run 2000 strengthens this interpretation because substantive MET/DRA/BBC files exist independently next to the realized SWP.

## Resolved hidden rule

ELAS is independently observed as 1e-6 in both realized oracle sets. This may originate in SWAPtools/template policy; provenance inside SWAPtools is still open, but realized output semantics are strongly bound.

RDS is not a fixed hidden default. It is run-dependent. The exact source/precedence rule still requires recovery from the datamodel/SWAPtools contract; historical regression must compare against the realized run value until that rule is qualified.

## Regression oracle policy

Generated SWP files are primary realized-output evidence for renderer equivalence. Compare semantic assignments and tables first; byte equality is secondary because whitespace/template comments are not scientific behavior.

The run-2000 oracle is suitable for the first direct-renderer one-run gate because:
1. the SWP is available as raw bytes;
2. its three external references are available as substantive raw files;
3. it contains nontrivial soil hydraulic rows;
4. it demonstrates a non-120 RDS value and therefore discriminates RDS authority hypotheses.
