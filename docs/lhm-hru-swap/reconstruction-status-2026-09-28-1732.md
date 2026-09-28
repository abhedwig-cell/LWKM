# LWKM reconstruction status — 28 September 2026 17:32 CEST

## Reconstructed historical chain

### Domain and SVAT preparation

1. **LHM/SVAT source state** — source tables and export contracts identified; exact S0 technical NL-baseline lineage still has an older/current row-count distinction (552,834 versus 552,705) to preserve in provenance.
2. **Agriculture+nature selection** — reconstructed authority: versioned land-use lookup, equivalent to `lu2 in {1,2}` in the bound historical data; 427,656 selected SVATs. The old 427,660 filter is a four-cell legacy error, not a rule.
3. **Flevoland** — observed kwel-only state transition `kwel_org -> kwel` on 4,677 SVATs, produced by Deltares postprocessing/editing of standard LHM output. Exact Deltares edit procedure remains provenance-only open.
4. **Hydrological qualification** — eight active flags identify exactly 20,934 suspected SVATs.

### HRU derivation

5. The 20,934 suspected SVATs are not intended as donor-value cluster observations. The R source restores their original target properties and excludes them from the valid cluster-building population.
6. Valid SVATs build clusters through 11 aggregation/relaxation rounds.
7. Suspected/rest targets are subsequently assigned through donor matching, first within LDGB×lu4, then LDGB×lu2, with extra-HRU construction for remaining cases.
8. Current output maps 427,656 SVATs to 10,242 HRUs and 25,054 NRUs.
9. HRU representative SVAT is a separate relation from both the initial suspected-target donor marker and the later cluster donor.
10. Exact R source, parameters and input checksums are bound; rerun is currently blocked by raw-byte access in this chat runtime, not by scientific uncertainty.

### HRU → SWAP

11. HRUlist2SWAP v0.38 source and production control are bound.
12. Production `HRU2SWAP.exe` embeds matching v0.38/apr-2026 identity and source path; exact compiler/build flags remain open.
13. Current `SVAT2SWAP10242.csv` contains 10,242 coherent cases and is consistent with tested v0.38 rules.
14. `export_HRUschema_10242_copy.csv` is a policy artifact, not a simple copy: for 2,559 HRUs it sets representative root-zone/soil fields to `-999`, disabling the representative override in v0.38. Exact producer rule remains open; affected HRUs are strongly associated with small/rest-group HRUs.
15. v0.38 mixes all-member, representative-SVAT and water-boundary-subset policies. Modern mapping must state the member/representation policy per SWAP target field.

### SWAP execution → ANIMO

16. Historical SWAP runner and result-extraction scripts are not present in the supplied material and were already recorded as missing in older LWKM process documentation.
17. Downstream products must distinguish native SWAP output, QA/LHM-comparison summaries and ANIMO hydrology exchange.
18. ANIMO hydrology is a compartment water-balance/flux contract historically associated with binary/unformatted `SWATRE.UNF`/SWAP-like exchange, not merely a CSV summary.

## Remaining high-value historical gaps

- exact Deltares Flevoland kwel-edit procedure;
- producer of the initial 20,934 suspected-target donor marker (its downstream role is now understood);
- exact producer/rationale of the 2,559 representative-override disable decisions;
- exact HRU10242 rerun when source bytes are executable in one runtime;
- SWAP runner, extraction/postprocessing and ANIMO exchange writer.

None of these gaps requires inventing missing scientific rules. The modern workflow can already be designed around explicit states, relations and policies while preserving the observed historical outputs as regression references.
