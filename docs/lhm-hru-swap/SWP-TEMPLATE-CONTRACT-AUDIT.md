# SWP template contract audit

Source: Tools(1).zip, Tools/SWAP/template/swap.swp and Datamodel_lwkm71c.sqlite.

The SWP template contains 27 Mustache-style symbols. Dynamic sections are concentrated in:
- TABLE_SOILPROFILE: ISUBLAY, ISOILLAY, HSUBLAY, NCOMP
- TABLE_SOILHYDRFUNC: ORES, OSAT, ALFA, NPAR, KSATFIT, LEXP, H_ENPR, KSATEXM, BDENS, ELAS
- TABLE_SOILTEXTURES: PSAND, PSILT, PCLAY, ORGMAT
- RDS
- SWBOTB and optional SWBOTB=2 DATE2/QBOT2 table.

The SQLite schema provides direct sources for nearly all of these through Runs, discretisatie and eigenschappen.

## Unresolved SWAPtools semantics found immediately

For run_id=1 in Datamodel_lwkm71c.sqlite:
- Runs.RDS = 25
- Wortelzone(soil_id=2001,crop_id=1).RDS = 100

Therefore RDS cannot be sourced safely without recovering create_SWAP precedence.

The template expects ELAS per hydraulic layer, but this SQLite eigenschappen table has no ELAS column. A hidden default/version rule exists somewhere in SWAPtools or template handling.

The template itself also contains many non-placeholder settings (TSTART/TEND, METFIL, crop rotation, initial conditions, drainage references etc.) that are likely modified by create_SWAP after or during rendering. Those must be audited before semantic equivalence is claimed.

## Policy

Python replacement is fail-closed:
- no guessed ELAS;
- no guessed RDS precedence;
- no SWP write while unresolved fields remain.

The context builder can already expose all source records and conflicts. This is used to recover the remaining create_SWAP contract systematically.
