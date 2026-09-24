# Hydrological effect decomposition

The project-leader table is retained, but each row now has one explicit scientific meaning. This matters because a change in a national balance can come from very different causes.

## The seven reporting stages

| Stage | What changes? | What the reported difference means |
|---|---|---|
| LHM4.3 | baseline | upstream hydrologic reference |
| LHM4.3 lbn | population | effect of selecting the LWKM domain |
| LHM4.3 cor | values, same SVATs | effect of an explicit hydrologic correction |
| LHM4.3 rep | use/replacement policy | effect of handling implausible SVAT hydrology |
| LWKM SVATs | model translation | 1:1 LHM→SWAP effect on HRU representative SVATs |
| LWKM HRUs | representation + mapping | effect of converting many SVATs into one HRU and building SWAP inputs |
| LWKM rep | HRU-result policy | effect of any explicit qualification/replacement of anomalous HRU/SWAP results |

The machine-readable authority is `config/effects/project-leader-stages.yml`.

## Why the representative-SVAT experiment is useful

The current HRU procedure produces both donor relations and a separate `svat_repr`. The canonical 1:1 experiment uses `svat_repr`, unless a later authority deliberately changes that.

For HRU h, let r(h) be its representative SVAT.

We calculate:

LHM(r(h)) → SWAP_1to1(r(h))

without first averaging the other SVATs in the HRU. The difference tells us what happens when the representative LHM case is translated into SWAP.

For national summaries the result is weighted by the area represented by each HRU, not by counting each representative SVAT once.

## HRU effect should be decomposed three ways

A single "HRU effect" hides too much. We should retain three comparisons.

### A. Representation before SWAP

Compare the area-weighted hydrology of all qualified LHM SVATs in an HRU with the hydrologic representation that is fed to SWAP.

This reveals what aggregation and representative choices do before SWAP solves anything.

### B. Representative-SVAT SWAP versus HRU SWAP

Compare the 1:1 SWAP run for the representative SVAT with the final HRU SWAP run.

This reveals the effect of HRU input construction within SWAP: averaging, mapping, drainage construction, boundary construction, meteorology and similar rules.

### C. Total LHM versus HRU SWAP

Compare area-weighted qualified LHM hydrology with the final HRU SWAP result.

This is the operational end-to-end difference, but it should only be reported together with A and B so its origin remains understandable.

## Feedback loop after SWAP

If SWAP QA finds a new unrealistic result, there are two possibilities.

1. The SWAP/HRU mapping is wrong or inadequate. Then a new mapping candidate is made and only SWAP_INPUT and downstream products are rerun.
2. The problem is already present in the upstream LHM/SVAT hydrology. Then a new qualification or correction candidate is created upstream and all affected downstream steps are rerun.

The old run remains intact in both cases. The new run receives a new run-id and is compared against its parent.

This is how the workflow supports research cycles without becoming an accumulation of manually edited files.
